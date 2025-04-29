#ifndef HCONFIG_H_
#define HCONFIG_H_

#define FAST_BUILD
#define ZLIB_FOUND
#define CUPDLP_CPU
/* #undef CUPDLP_GPU */
/* #undef CUPDLP_FORCE_NATIVE */
#define CMAKE_BUILD_TYPE "Release"
#define CMAKE_INSTALL_PREFIX "/workspace/destdir"
/* #undef HIGHSINT64 */
/* #undef HIGHS_NO_DEFAULT_THREADS */
#define HIGHS_HAVE_MM_PAUSE
#define HIGHS_HAVE_BUILTIN_CLZ
/* #undef HIGHS_HAVE_BITSCAN_REVERSE */

#define HIGHS_GITHASH "fd8665394e"
#define HIGHS_VERSION_MAJOR 1
#define HIGHS_VERSION_MINOR 10
#define HIGHS_VERSION_PATCH 0
#define HIGHS_DIR "/workspace/srcdir/HiGHS"

#endif /* HCONFIG_H_ */
