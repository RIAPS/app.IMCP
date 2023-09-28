/*****************************************************************************/
/* crc_tbl.h v6.4.12                                                         */
/*                                                                           */
/* Copyright (c) 2010-2017 Texas Instruments Incorporated                    */
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
/*                                                                           */
/* Specification of CRC table data structures which can be automatically     */
/* generated by the linker (using the crc_table() operator in the linker     */
/* command file).                                                            */
/*****************************************************************************/
/*****************************************************************************/
/*                                                                           */
/*  The CRC generator used by the linker is based on concepts from the       */
/*  document:                                                                */
/*     "A Painless Guide to CRC Error Detection Algorithms"                  */
/*                                                                           */
/* Author : Ross Williams (ross@guest.adelaide.edu.au.).                     */
/* Date   : 3 June 1993.                                                     */
/* Status : Public domain (C code).                                          */
/*                                                                           */
/* Description : For more information on the Rocksoft^tm Model CRC           */
/* Algorithm, see the document titled "A Painless Guide to CRC Error         */
/* Detection Algorithms" by Ross Williams (ross@guest.adelaide.edu.au.).     */
/* This document is likely to be in "ftp.adelaide.edu.au/pub/rocksoft" or    */
/* at http:www.ross.net/crc/download/crc_v3.txt.                             */
/*                                                                           */
/* Note: Rocksoft is a trademark of Rocksoft Pty Ltd, Adelaide, Australia.   */
/*****************************************************************************/

#include <stdint.h>        /* For uintXX_t */

/*****************************************************************************/
/* CRC Algorithm Specifiers                                                  */
/*                                                                           */
/* The following specifications, based on the above cited document, are used */
/* by the linker to generate CRC values.                                     */
/*                                                                           */
/*                                                                           */
/* ID  Name          Order  Polynomial   Initial     Ref Ref  CRC XOR   Zero */
/*                                       Value       In  Out  Value     Pad  */
/*-------------------------------------------------------------------------- */
/* 0, "CRC32_PRIME",    32, 0x04c11db7,  0x00000000,  0,  0, 0x00000000,  1  */
/* 1, "CRC16_802_15_4", 16, 0x00001021,  0x00000000,  0,  0, 0x00000000,  1  */
/* 2, "CRC16_ALT",      16, 0x00008005,  0x00000000,  0,  0, 0x00000000,  1  */
/* 3, "CRC8_PRIME",      8, 0x00000007,  0x00000000,  0,  0, 0x00000000,  1  */
/* 11,"CRC32",          32, 0x1edc6f41,  0x00000000,  0,  0, 0x00000000,  1  */
/* 12,"CRC24_FLEXRAY",  24, 0x005d6dcb,  0x00000000,  0,  0, 0x00000000,  1  */
/*                                                                           */
/* Users should specify the name, such as CRC32_PRIME, in the linker command */
/* file.  The resulting CRC_RECORD structure will contain the corresponding  */
/* ID value in the crc_alg_ID field. The ID needs to match the enum value    */
/* CRC_CONFIG_TYPE in crc.h, which is the index into the crc_configs_m table.*/
/*****************************************************************************/
#define CRC32_PRIME	  0	/* Poly = 0x04c11db7 */ /* DEFAULT ALGORITHM */
#define CRC16_802_15_4	  1	/* Poly = 0x00001021 */
#define CRC16_ALT	  2	/* Poly = 0x00008005 */
#define CRC8_PRIME	  3	/* Poly = 0x00000007 */
#define CRC32_C           11     /* Poly = 0x1edc6f41 */
#define CRC24_FLEXRAY     12     /* Poly = 0x005d6dcb */

/****************************************************************************/
/* CRC Record Data Structure                                                */
/* NOTE: The list of fields and the size of each field varies by target     */
/*       and memory model.                                                  */
/****************************************************************************/
typedef struct crc_record
{
uint16_t         crc_alg_ID;    /* CRC algorithm ID                         */
uint16_t         page_id;       /* page number of data                      */
uint32_t         addr;          /* Starting address                         */
uint32_t         size;          /* size of data in 16-bit addressable units */
uint32_t         crc_value;
} CRC_RECORD;

 
/**********************************************************/
/* CRC Table Data Structure                               */
/**********************************************************/
typedef struct crc_table
{
uint16_t         rec_size;    /* 16-bit addressable units */
uint16_t         num_recs;
CRC_RECORD       recs[1];
} CRC_TABLE;


