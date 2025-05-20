import numpy as np
import threading
import queue # Per recuperare i risultati dal thread in modo sicuro
import time
import json
import os
import sys
from z3 import Z3Exception

def read_raw_instances(path:str):
    filename = "".join(path.split('/')[-1].split('.')[:-1])
    with open(path, 'r') as f:
        matrix = ''
        for i, line in enumerate(f):
            if i == 0:
                m = int(line)
            elif i == 1:
                n = int(line)
            elif i == 2:
                l = [int(x) for x in line.split() if x.strip()]   # load
            elif i == 3:
                s = [int(x) for x in line.split() if x.strip()]   # item size
            else:
                matrix += line[:-1] + '; '
    d = np.matrix(matrix[:-2]).tolist()
    return filename,m,n,l,s,d

def run_z3_with_external_timeout(external_timeout_seconds, model_func, *args, **kwargs):
    """
    Esegue una funzione modello Z3 (come my_model) in un thread separato
    con un timeout esterno.
    Args:
        external_timeout_seconds (float): Timeout in secondi.
        model_func (callable): La funzione che costruisce e risolve il modello Z3 (es. my_model).
                               Deve accettare un kwarg 'opt_container'.
        *args: Argomenti posizionali per model_func.
        **kwargs: Argomenti keyword per model_func.
    Returns:
        dict: Il risultato da model_func o un dizionario di errore/timeout.
    """
    result_queue = queue.Queue()
    opt_instance_container = [None] # Lista usata come contenitore mutabile

    # Assicurati che 'opt_container' sia passato a model_func
    kwargs_for_model = kwargs.copy()
    kwargs_for_model['opt_container'] = opt_instance_container

    def worker():
        try:
            # Esegui la funzione modello
            res = model_func(*args, **kwargs_for_model)
            result_queue.put(res)
        except Z3Exception as z3e:
            # Se Z3 viene interrotto, solleva una Z3Exception
            print(f"Z3Exception nel worker: {z3e}")
            result_queue.put({
                'solution_found': False, 
                'status': 'z3_exception_in_worker',
                'error': str(z3e),
                'reason_unknown': 'interrupted' if 'interrupted' in str(z3e).lower() else str(z3e)
            })
        except Exception as e:
            print(f"Errore generico nel worker: {e}")
            result_queue.put({
                'solution_found': False, 
                'status': 'error_in_worker', 
                'error': str(e)
            })

    thread = threading.Thread(target=worker)
    thread.daemon = True # Permette al programma principale di uscire anche se il thread è bloccato
    
    start_execution_time = time.time()
    thread.start()
    thread.join(timeout=external_timeout_seconds)
    
    actual_execution_time = time.time() - start_execution_time

    if thread.is_alive():
        print(f"Timeout esterno di {external_timeout_seconds}s scaduto. Tentativo di interruzione del solver Z3...")
        solver_to_interrupt = opt_instance_container[0]
        interrupted_internally = False
        if solver_to_interrupt:
            try:
                solver_to_interrupt.interrupt()
                print("Segnale di interruzione inviato a Z3.")
                interrupted_internally = True
            except Exception as e:
                print(f"Errore durante l'invio dell'interruzione a Z3: {e}")
        else:
            print("Nessuna istanza di solver Z3 trovata da interrompere (potrebbe essere terminato o non aver ancora chiamato check).")

        # Dai al thread un momento per processare l'interruzione e terminare
        # Se interrupt() è stato chiamato, check() dovrebbe sollevare Z3Exception o restituire unknown
        additional_wait_time = 2.0 # Secondi
        thread.join(timeout=additional_wait_time)

        if thread.is_alive():
            print(f"Il thread è ancora attivo dopo il tentativo di interruzione e {additional_wait_time}s di attesa aggiuntiva. Z3 potrebbe essere irresponsivo.")
            return {
                'solution_found': False, 
                'status': 'timeout_external_stuck_after_interrupt',
                'time': actual_execution_time + additional_wait_time,
                'reason_unknown': 'external_timeout_thread_stuck'
            }
        else:
            print("Il thread è terminato dopo l'interruzione.")
            try:
                # Il worker potrebbe aver messo un risultato dopo l'interruzione (es. gestendo Z3Exception)
                result = result_queue.get_nowait()
                if 'time' not in result: result['time'] = actual_execution_time # Aggiorna il tempo se non presente
                if interrupted_internally and 'status' in result and result['status'] != 'z3_exception_in_worker':
                    # Se Z3 ha restituito unknown a causa dell'interrupt, marchiamolo
                    if result.get('status') == 'unknown':
                         result['reason_unknown'] = result.get('reason_unknown', '') + '; external_interrupt_attempted'
                    result['status'] += '_after_external_interrupt'

                # Se il modello ha restituito 'unknown' a causa dell'interrupt, aggiorniamo il motivo
                if result.get('status', '').startswith('unknown') and 'reason_unknown' in result:
                    result['reason_unknown'] = f"External interrupt likely cause: {result['reason_unknown']}"
                elif result.get('status', '').startswith('unknown'):
                     result['reason_unknown'] = "External interrupt likely cause"
                
                return result
            except queue.Empty:
                # Questo può accadere se l'interrupt ha causato l'uscita brusca del thread
                # o se il worker non ha gestito l'eccezione dell'interrupt mettendo un risultato.
                return {
                    'solution_found': False, 
                    'status': 'timeout_external_interrupted_no_result_in_queue',
                    'time': actual_execution_time,
                    'reason_unknown': 'external_timeout_no_result_after_interrupt'
                }
    else:
        # Il thread è terminato da solo entro il timeout esterno
        print("Il thread è terminato autonomamente entro il timeout esterno.")
        try:
            result = result_queue.get_nowait()
            if 'time' not in result: result['time'] = actual_execution_time
            return result
        except queue.Empty:
            # Non dovrebbe accadere se il thread è terminato correttamente e il worker ha messo un risultato
            return {
                'solution_found': False, 
                'status': 'thread_completed_no_result_in_queue',
                'time': actual_execution_time,
                'error': 'Worker thread finished but no result was found in the queue.'
            }
        
def write_output(results, output_path): # Allow customizing approach name
    """Writes the results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w') as f:
            output_data = {"z3": results}
            json.dump(output_data, f, indent=4)
        print(f"Results written to {output_path}")
    except Exception as e:
        print(f"Error writing output file {output_path}: {e}", file=sys.stderr)

def combine_results(result_nosymbreak_dir, result_symbreak_dir):
    
    combined_results = {}
    
    for results_file in sorted(os.listdir(result_nosymbreak_dir)):
        if results_file.startswith('.'):
            # Skip hidden folders.
            continue
        if results_file not in combined_results.keys():
            combined_results[results_file] = {}
        
        updated_results = {}
        results = json.load(open(os.path.join(result_nosymbreak_dir, results_file)))
        updated_results = {'z3': results['z3']}
        combined_results[results_file].update(updated_results)
    
    for results_file in sorted(os.listdir(result_symbreak_dir)):
        if results_file.startswith('.'):
            # Skip hidden folders.
            continue
        if results_file not in combined_results.keys():
            combined_results[results_file] = {}
        
        updated_results = {}
        results = json.load(open(os.path.join(result_symbreak_dir, results_file)))
        updated_results = {'z3_symbreak': results['z3']}
        combined_results[results_file].update(updated_results)
    
    # Write combined results to a single JSON file
    os.makedirs("res/SMT", exist_ok=True)

    for file_name, result in combined_results.items():
        output_path = os.path.join("res/SMT", file_name)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=4)
        print(f"Combined results written to {output_path}")