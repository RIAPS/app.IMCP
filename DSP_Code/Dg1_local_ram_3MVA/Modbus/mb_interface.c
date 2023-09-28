/*
 * FreeModbus Libary: MSP430 Demo Application
 * Copyright (C) 2006 Christian Walter <wolti@sil.at>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * File: $Id: demo.c,v 1.3 2006/11/19 15:22:40 wolti Exp $
 */

/* ----------------------- Platform includes --------------------------------*/
#include "port.h"
#include "string.h"
#include <math.h>
/* ----------------------- Modbus includes ----------------------------------*/
#include "mb.h"
#include "mbport.h"
#include "mb_interface.h"
#define pi  3.141592653589793


/* ----------------------- Defines ------------------------------------------*/
#define MB_SLAVE_ID						(0x0A)
#define MB_BAUD_RATE					(115200)

#define REG_INPUT_START   				(0)
#define REG_INPUT_NREGS   				(30U)

#define REG_HOLDING_START 				(2000)
#define REG_HOLDING_NREGS 				(9U)


/* ----------------------- Static variables ---------------------------------*/
static USHORT   usRegInputStart = REG_INPUT_START;
static USHORT   usRegInputBuf[REG_INPUT_NREGS];
static USHORT   usRegHoldingStart = REG_HOLDING_START;
static USHORT   usRegHoldingBuf[REG_HOLDING_NREGS];
eMBErrorCode    eStatus;


//information exchange between main and modbus



//extern volatile Uint16 Start_Stop_modbus;
//extern volatile Uint16 islanding_mode_modbus;
//extern volatile Uint16 secondary_control_enable_modbus;

extern volatile float angularFrequency_modbus;
// commands for modbus holding registers
extern volatile USHORT ControlWord_modbus;          // holding register 2000
extern volatile float Pcommand_modbus;             // holding register 2001
extern volatile float Qcommand_modbus;             // holding register 2002
extern volatile float Vcommand_modbus;             // holding register 2003
extern volatile float Fcommand_modbus;             // holding register 2004
extern volatile float VQdroop_command_modbus;      // holding register 2005
extern volatile float FPdroop_command_modbus;      // holding register 2006
extern volatile float FaultAutoRstTime_modbus;     // holding register 2007

// measurements for modbus input registers
extern volatile float Ia_peak_modbus;     // Input register 0
extern volatile float Ia_angle_modbus;    // Input register 1
extern volatile float Ib_peak_modbus;     // Input register 2
extern volatile float Ib_angle_modbus;    // Input register 3
extern volatile float Ic_peak_modbus;     // Input register 4
extern volatile float Ic_angle_modbus;    // Input register 5
extern volatile float Ia_rms_modbus;      // Input register 6
extern volatile float Ib_rms_modbus;      // Input register 7
extern volatile float Ic_rms_modbus;      // Input register 8
extern volatile float Va_rms_modbus;      // Input register 9
extern volatile float Vb_rms_modbus;      // Input register 10
extern volatile float Vc_rms_modbus;      // Input register 11
extern volatile float Va_peak_modbus;     // Input register 12
extern volatile float Va_angle_modbus;    // Input register 13
extern volatile float Vb_peak_modbus;     // Input register 14
extern volatile float Vb_angle_modbus;    // Input register 15
extern volatile float Vc_peak_modbus;     // Input register 16
extern volatile float Vc_angle_modbus;    // Input register 17
extern volatile float activePower_modbus; // Input register 18
extern volatile float reactivePower_modbus;     // Input register 19
extern volatile float apparentPower_modbus;     // Input register 20
extern volatile float powerFactor_modbus; // Input register 21
extern volatile float frequency_modbus;    // Input register 22
extern volatile float sync_freq_slip_modbus;     // Input register 23
extern volatile float sync_volt_diff_modbus;     // Input register 24
extern volatile float sync_ang_diff_modbus;      // Input register 25
extern volatile USHORT status_modbus;  // Input register 26
//extern volatile USHORT fault_status_modbus;  // Input register 27
extern volatile float vref_modbus; // Input register 27
extern volatile float wref_modbus; // Input register 28

static void MBUpdateData(void);
/* ----------------------- Start implementation -----------------------------*/

/*
*******************************************************************************
* void ModbusInit(void)
*******************************************************************************
* Input         : void
* Output        : void
* Description   : Main Function for HUPS project.
*******************************************************************************
*/

void ModbusInit(void)
{
	eStatus = eMBInit(MB_RTU, MB_SLAVE_ID, 0, MB_BAUD_RATE, MB_PAR_NONE);
	eStatus = eMBEnable();
	//Initialize all the registers to zero
	memset(usRegHoldingBuf, 0, sizeof(usRegHoldingBuf));
	memset(usRegInputBuf, 0, sizeof(usRegInputBuf));


}// End of ModbusInit


/*
*******************************************************************************
* void ModbusPoll(void)
*******************************************************************************
* Input         : void
* Output        : void
* Description   :
*******************************************************************************
*/

void ModbusPoll(void)
{
	MBUpdateData();
	(void)eMBPoll();
}// End of ModbusPoll

/*
*******************************************************************************
* eMBErrorCode eMBRegHoldingCB( UCHAR * pucRegBuffer, USHORT usAddress,
* 								USHORT usNRegs, eMBRegisterMode eMode )
*******************************************************************************
* Input         : void
* Output        : void
* Description   :
*******************************************************************************
*/

void MBUpdateData(void)
{
	//Because of the way the MODBUS protocol is defined, the index locations '0' for usRegInputBuf and usRegHoldingBuf shall be unutilized.
	//Thus in the example below, usRegInputBuf[0], though assigned a value of 20 in the code here, doesn't make any difference as far as the Modbus Master is concerned.
	//Modbus Master will never be able to poll for usRegInputBuf[0]. Hence the assignment here is redundant.

	usRegInputBuf[0] 		= 20; // this useless as mentioned above

	usRegInputBuf[1] 		=  Ia_peak_modbus;     // Input register 0
	usRegInputBuf[2] 		=  (SHORT) (Ia_angle_modbus*10);    // Input register 1
	usRegInputBuf[3] 		=  Ib_peak_modbus;     // Input register 2
	usRegInputBuf[4] 		=  (SHORT) (Ib_angle_modbus*10);    // Input register 3
	usRegInputBuf[5] 		=  Ic_peak_modbus;     // Input register 4
	usRegInputBuf[6] 		=  (SHORT) (Ic_angle_modbus*10);    // Input register 5
	usRegInputBuf[7] 		=  Ia_rms_modbus;      // Input register 6
	usRegInputBuf[8] 		=  Ib_rms_modbus;      // Input register 7
	usRegInputBuf[9] 		=  Ic_rms_modbus;      // Input register 8
	usRegInputBuf[10] 		=  Va_rms_modbus;      // Input register 9
	usRegInputBuf[11] 		=  Vb_rms_modbus;      // Input register 10
	usRegInputBuf[12] 		=  Vc_rms_modbus;      // Input register 11
	usRegInputBuf[13] 		=  Va_peak_modbus;     // Input register 12
	usRegInputBuf[14] 		=  (SHORT) (Va_angle_modbus*10);    // Input register 13
	usRegInputBuf[15] 		=  Vb_peak_modbus;     // Input register 14
	usRegInputBuf[16] 		=  (SHORT) (Vb_angle_modbus*10);    // Input register 15
	usRegInputBuf[17] 		=  Vc_peak_modbus;     // Input register 16
	usRegInputBuf[18] 		=  (SHORT) (Vc_angle_modbus*10);    // Input register 17
	usRegInputBuf[19] 		=  (SHORT) (activePower_modbus); // Input register 18
	usRegInputBuf[20] 		=  (SHORT) (reactivePower_modbus);     // Input register 19
	usRegInputBuf[21] 		=  apparentPower_modbus;     // Input register 20
	usRegInputBuf[22] 		=  (SHORT) (powerFactor_modbus*1000);       // Input register 21
	usRegInputBuf[23] 		=  frequency_modbus*100;         // Input register 22
	usRegInputBuf[24] 		=  sync_freq_slip_modbus*100;    // Input register 23
	usRegInputBuf[25] 		=  sync_volt_diff_modbus;    // Input register 24
	usRegInputBuf[26] 		=  sync_ang_diff_modbus*10;     // Input register 25
	usRegInputBuf[27] 		=  status_modbus;            // Input register 26
	usRegInputBuf[28] 		=  vref_modbus*1000;      // Input register 27
    usRegInputBuf[29]       =  wref_modbus*1000;            // Input register 28


	// this is the start and stop command
/*
	if (usRegHoldingBuf[1] == 1)
	{
		Start_Stop_modbus  = 1;
		islanding_mode_modbus = 0;
		secondary_control_enable_modbus = 0;

	}
	else if (usRegHoldingBuf[1] == 3)
	{
		Start_Stop_modbus  = 1;
		islanding_mode_modbus = 1;
		secondary_control_enable_modbus = 0;
	}
	else if (usRegHoldingBuf[1] == 7)
	{
		Start_Stop_modbus  = 1;
		islanding_mode_modbus = 1;
		secondary_control_enable_modbus = 1;
	}
	else
	{
		Start_Stop_modbus  = 0;
		islanding_mode_modbus = 0;
		secondary_control_enable_modbus = 0;
	}
*/
	ControlWord_modbus = usRegHoldingBuf[1];            // holding register 2000
	Pcommand_modbus   = (SHORT) usRegHoldingBuf[2];             // holding register 2001
	Qcommand_modbus   = (SHORT) usRegHoldingBuf[3];             // holding register 2002
	Vcommand_modbus   = usRegHoldingBuf[4];             // holding register 2003
	Fcommand_modbus   = usRegHoldingBuf[5]*0.001;             // holding register 2004
	VQdroop_command_modbus   = usRegHoldingBuf[6]*0.01;      // holding register 2005
	FPdroop_command_modbus   = usRegHoldingBuf[7]*0.01;      // holding register 2006
	FaultAutoRstTime_modbus   = usRegHoldingBuf[8];     // holding register 2007


}// End of MBUpdateData


/*
*******************************************************************************
* eMBErrorCode eMBRegInputCB( UCHAR * pucRegBuffer, USHORT usAddress, USHORT usNRegs )
*******************************************************************************
* Input         : void
* Output        : void
* Description   :
*******************************************************************************
*/

eMBErrorCode eMBRegInputCB( UCHAR * pucRegBuffer, USHORT usAddress, USHORT usNRegs )
{
    eMBErrorCode    eStatus = MB_ENOERR;
    int             iRegIndex;

    if( ( usAddress >= REG_INPUT_START )
        && ( usAddress + usNRegs <= REG_INPUT_START + REG_INPUT_NREGS ) )
    {
        iRegIndex = ( int )( usAddress - usRegInputStart );
        while( usNRegs > 0 )
        {
            *pucRegBuffer++ = ( unsigned char )( usRegInputBuf[iRegIndex] >> 8 );
            *pucRegBuffer++ = ( unsigned char )( usRegInputBuf[iRegIndex] & 0xFF );
            iRegIndex++;
            usNRegs--;
        }
    }
    else
    {
        eStatus = MB_ENOREG;
    }

    return eStatus;
}


/*
*******************************************************************************
* eMBErrorCode eMBRegHoldingCB( UCHAR * pucRegBuffer, USHORT usAddress,
* 								USHORT usNRegs, eMBRegisterMode eMode )
*******************************************************************************
* Input         : void
* Output        : void
* Description   :
*******************************************************************************
*/

eMBErrorCode eMBRegHoldingCB( UCHAR * pucRegBuffer, USHORT usAddress,
							  USHORT usNRegs, eMBRegisterMode eMode )
{
    eMBErrorCode    eStatus = MB_ENOERR;
    int             iRegIndex;

    if( ( usAddress >= REG_HOLDING_START ) &&
        ( usAddress + usNRegs <= REG_HOLDING_START + REG_HOLDING_NREGS ) )
    {
        iRegIndex = ( int )( usAddress - usRegHoldingStart );
        switch ( eMode )
        {
            /* Pass current register values to the protocol stack. */
        case MB_REG_READ:
            while( usNRegs > 0 )
            {
                *pucRegBuffer++ = ( unsigned char )( usRegHoldingBuf[iRegIndex] >> 8 );
                *pucRegBuffer++ = ( unsigned char )( usRegHoldingBuf[iRegIndex] & 0xFF );
                iRegIndex++;
                usNRegs--;
            }
            break;

            /* Update current register values with new values from the
             * protocol stack. */
        case MB_REG_WRITE:
            while( usNRegs > 0 )
            {
                usRegHoldingBuf[iRegIndex] = *pucRegBuffer++ << 8;
                usRegHoldingBuf[iRegIndex] |= *pucRegBuffer++;
                iRegIndex++;
                usNRegs--;
            }
        }
    }
    else
    {
        eStatus = MB_ENOREG;
    }
    return eStatus;
}

eMBErrorCode
eMBRegCoilsCB( UCHAR * pucRegBuffer, USHORT usAddress, USHORT usNCoils, eMBRegisterMode eMode )
{
    return MB_ENOREG;
}

eMBErrorCode
eMBRegDiscreteCB( UCHAR * pucRegBuffer, USHORT usAddress, USHORT usNDiscrete )
{
    return MB_ENOREG;
}
