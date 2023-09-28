/*****************************************************************************/
/* math.h     v6.4.12                                                        */
/*                                                                           */
/* Copyright (c) 1996-2017 Texas Instruments Incorporated                    */
/* http://www.ti.com/                                                        */
/*                                                                           */
/*  Redistribution and  use in source  and binary forms, with  or without    */
/*  modification,  are permitted provided  that the  following conditions    */
/*  are met:                                                                 */
/*                                                                           */
/*     Redistributions  of source  code must  retain the  above copyright    */
/*     notice, this list of conditions and the following disclaimer.         */
/*                                                                           */
/*     Redistributions in binary form  must reproduce the above copyright    */
/*     notice, this  list of conditions  and the following  disclaimer in    */
/*     the  documentation  and/or   other  materials  provided  with  the    */
/*     distribution.                                                         */
/*                                                                           */
/*     Neither the  name of Texas Instruments Incorporated  nor the names    */
/*     of its  contributors may  be used to  endorse or  promote products    */
/*     derived  from   this  software  without   specific  prior  written    */
/*     permission.                                                           */
/*                                                                           */
/*  THIS SOFTWARE  IS PROVIDED BY THE COPYRIGHT  HOLDERS AND CONTRIBUTORS    */
/*  "AS IS"  AND ANY  EXPRESS OR IMPLIED  WARRANTIES, INCLUDING,  BUT NOT    */
/*  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR    */
/*  A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT    */
/*  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,    */
/*  SPECIAL,  EXEMPLARY,  OR CONSEQUENTIAL  DAMAGES  (INCLUDING, BUT  NOT    */
/*  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,    */
/*  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY    */
/*  THEORY OF  LIABILITY, WHETHER IN CONTRACT, STRICT  LIABILITY, OR TORT    */
/*  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE    */
/*  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.     */
/*                                                                           */
/*****************************************************************************/

#ifndef _MATH
#define _MATH

#if defined(__TMS320C28XX_CLA__)
#error "Header file <math.h> not supported by CLA compiler"
#endif

#include <linkage.h>

#pragma diag_push
#pragma CHECK_MISRA("-6.3") /* standard types required for standard headers */
#pragma CHECK_MISRA("-8.5") /* need to define inline function */
#pragma CHECK_MISRA("-8.11") /* need to use __inline as is */
#pragma CHECK_MISRA("-19.7") /* macros required for implementation */
#pragma CHECK_MISRA("-20.1") /* standard headers must define standard names */
#pragma CHECK_MISRA("-20.2") /* standard headers must define standard names */

#define HUGE_VALF  (__INFINITY__)
#define HUGE_VAL   ((double)__INFINITY__)
#define HUGE_VALL  ((long double)__INFINITY__)
#define NAN        (__NAN__)
#define INFINITY   (__INFINITY__)

#ifdef __cplusplus
//----------------------------------------------------------------------------
// <cmath> IS RECOMMENDED OVER <math.h>.  <math.h> IS PROVIDED FOR 
// COMPATIBILITY WITH C AND THIS USAGE IS DEPRECATED IN C++
//----------------------------------------------------------------------------
extern "C" namespace std {
#endif /* __cplusplus */

/* simplistic isinf and isnan */
#define isinf(x) ((x) == INFINITY || (x) == -INFINITY)
#define isnan(x) ((x) != (x))

/***************************************************************/
/* TMU SUPPORT AND RELAXED MODE: USE INSTRINSICS.              */
/***************************************************************/
#if defined(__TMS320C28XX_TMU__)  && !__TI_STRICT_FP_MODE__

#pragma diag_push

/* keep macros as direct #defines and not function-like macros or function
   names surrounded by parentheses to support all original supported use cases
   including taking their address through the macros and prefixing with
   namespace macros */
#pragma CHECK_MISRA("-19.4")

#define sqrt  __relaxed_sqrt
__inline double __relaxed_sqrt(double x);
__inline double __relaxed_sqrt(double x)
{ 
    return __sqrt(x);  
}
#define sin   __relaxed_sin
__inline double __relaxed_sin(double x);
__inline double __relaxed_sin(double x)
{ 
    return __sin(x);  
}
#define cos   __relaxed_cos
__inline double __relaxed_cos(double x);
__inline double __relaxed_cos(double x)
{ 
    return __cos(x);  
}
#define atan  __relaxed_atan
__inline double __relaxed_atan(double x);
__inline double __relaxed_atan(double x)
{ 
  return __atan2(x,1.);
}
#define atan2 __relaxed_atan2
__inline double __relaxed_atan2(double y, double x);
__inline double __relaxed_atan2(double y, double x)
{ 
  return __atan2(y,x);
}

#pragma diag_pop

#endif /* defined(__TMS320C28XX_TMU__)  && !__TI_STRICT_FP_MODE__ */


/***************************************************************/
/* FUNCTION DEFINITIONS.                                       */
/***************************************************************/
         double modf(double x, double *y); 
    #if !defined(__cplusplus)
         double far_modf(double x, double *y); 
    #endif
         double asin(double x);
         double acos(double x);
         double atan(double x);
         double atan2(double y, double x);

__inline double ceil(double x);
__inline double ceil(double x)
         {
             double ceil_result;
             double ceil_y;
#pragma diag_push
#pragma diag_suppress 551 /* must be uninitialized to work around bug */
#pragma CHECK_MISRA("-9.1") /* must be uninitialized to work around bug */
#pragma CHECK_MISRA("-10.2") /* false positive on pointer-to-double param */
             if(modf(x, &ceil_y) > 0.)
#pragma diag_pop
             {
                 ceil_result = ceil_y + 1.;
             }
             else
             {
                 ceil_result = ceil_y;
             }
             return ceil_result;
         }

         double cos(double x);
         double cosh(double x);
         double exp(double x);
#pragma diag_push
#pragma CHECK_MISRA("-16.4") /* false positives due to builtin declarations */
         double fabs(double x);
#pragma diag_pop

__inline double floor(double x);
__inline double floor(double x)
         {
             double floor_result;
             double floor_y;
#pragma diag_push
#pragma diag_suppress 551 /* must be uninitialized to work around bug */
#pragma CHECK_MISRA("-9.1") /* must be uninitialized to work around bug */
#pragma CHECK_MISRA("-10.2") /* false positive on pointer-to-double param */
             if(modf(x, &floor_y) < 0.)
#pragma diag_pop
             {
                 floor_result = floor_y - 1.;
             }
             else
             {
                 floor_result = floor_y;
             }
             return floor_result;
         }

         double fmod(double x, double y);
         double frexp(double x, int *_exp);
    #if !defined(__cplusplus)
         double far_frexp(double x, int *_exp);
    #endif
         double ldexp(double x, int _exp);
         double log(double x);
         double log10(double x);
         double pow(double x, double y);
         double sin(double x);
         double sinh(double x);
         double tan(double x);
         double tanh(double x);
         double sqrt(double x);

#ifdef __cplusplus
} /* extern "C" namespace std */
#endif /* __cplusplus */

#pragma diag_pop

/******************************************************************************/
/*  Overloaded version of math functions for float and long double removed    */
/*  from here, and include in cmath instead (see Section 26.5 of C++ standard */
/*  for details). Thus cpp_inline_math.h is now included in cmath .           */
/******************************************************************************/
#endif /* _MATH */

#pragma diag_push

/* using declarations must occur outside header guard to support including both
   C and C++-wrapped version of header; see _CPP_STYLE_HEADER check */
/* this code is for C++ mode only and thus also not relevant for MISRA */
#pragma CHECK_MISRA("-19.15")

#if defined(__cplusplus) && !defined(_CPP_STYLE_HEADER)
using std::modf;
using std::asin;
using std::acos;
using std::atan;
using std::atan2;
using std::ceil;
using std::cos;
using std::cosh;
using std::exp;
using std::fabs;
using std::floor;
using std::fmod;
using std::frexp;
using std::ldexp;
using std::log;
using std::log10;
using std::pow;
using std::sin;
using std::sinh;
using std::tan;
using std::tanh;
using std::sqrt;
#endif /* _CPP_STYLE_HEADER */

#pragma diag_pop
