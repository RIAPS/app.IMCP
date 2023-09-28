/*
 * main.c
 */
/* ----------------------- DSP includes ----------------------------------*/
#include "F28x_Project.h"  // Device Headerfile and Examples Include File
#include <math.h>

/* ----------------------- Modbus includes --------------------------------*/
#include "mb.h"
#include "port.h"
#include "mbport.h"
#include "mbrtu.h"
#include "mb_interface.h"

/* ----------------------- CAN includes --------------------------------*/
#include <stdint.h>
#include <stdbool.h>
#include "inc/hw_types.h"
#include "inc/hw_memmap.h"
#include "inc/hw_can.h"
#include "driverlib/can.h"

/* ----------------------- Control code includes --------------------------------*/
#include "initial_3MVA.h"
#define pi  3.141592653589793
#define Vbatt 120 //36

/*
// These are defined by the linker (see F28335.cmd)
extern Uint16 RamfuncsLoadStart;
extern Uint16 RamfuncsLoadEnd;
extern Uint16 RamfuncsRunStart;
*/
/*-------------------------------------------------------------------------*/

 /// globe variables
float T5000Hz = 2e-4;
float T10000Hz = 1e-4;
float mt_ac = 0;
float w60Hz = 376.9911184307752;
float C_Cap = 800e-6;
float L_fil = 150e-6;

float wC = 376.9911184307752*800e-6;
float wL = 376.9911184307752*150e-6;
int GPIO20_EN = 0;
int control_en = 0;
int LED_counter = 0;
// ADC variables
float adc_A[6], adc_B[6];
int gridtie_mode = 1;


//PLL variables
float phase_pll     = 0;
float anglefreq_pll = 0;
float freq_pll      = 0;
float Vd_pll        = 0;
float Vq_pll        = 0;
float Vmag_pll      = 0;
float phase_compensation = -2*pi*(60./5000)*0.5;
float phase_pll_compensated;
int grid_voltage_is_OK;
int Vc_is_Vg;
// power variables

int   droop_en = 0;
float Power_abc = 0;
float Qower_abc = 0;
float Power_abc_lpf = 0;
float Qower_abc_lpf = 0;
float Power_dq = 0;
float Qower_dq = 0;
float Power_dq_lpf = 0;
float Qower_dq_lpf = 0;

float anglefreq_droop = 0;
float Vmag_droop = 0;
float phase_droop = 0;
float Power_droop_ref = 3000;
float Qower_droop_ref = 3000;

// virtual impedance variables;
float Lvirtual = 1e-6;
float Rvirtual = 0;

// grid voltage variables
float Vgab, Vgbc, Vgca;
float Vga, Vgb, Vgc;

// capacitor voltage variables
float Vcab, Vcbc, Vcca, Vcca2;
float Vca, Vcb, Vcc;
float Vd_cap        = 0;
float Vq_cap        = 0;
float Vd_cap_lpf    = 0;
float Vq_cap_lpf    = 0;
float Vd_cap_ref    = 0;
float Vq_cap_ref    = 0;

// filter current variables
float Ifa, Ifb, Ifc;
float Id_fil, Iq_fil;
float Id_fil_lpf, Iq_fil_lpf;
float Id_fil_ref    = 0;
float Iq_fil_ref    = 0;

// modulation variables
float md           = 0;
float mq           = 0;
float ma_unlimited = 0;
float mb_unlimited = 0;
float mc_unlimited = 0;
float ma_limited   = 0;
float mb_limited   = 0;
float mc_limited   = 0;


///communication variables for MODBUS
Uint16 Pcommand_modbus;
Uint16 Start_Stop_modbus = 0;
Uint16 islanding_mode_modbus = 0;
Uint16 secondary_control_enable_modbus = 0;

float Pcommand_modbus_float;
float omegaSecCtrl_modbus_float;
float eSecCtrl_modbus_float;

float own_secondary_variable = 0;
float angularFrequency_modbus;
float voltageMag_modbus;
float mP_modbus;
float reactivePower_modbus;

float IL1_modbus[2], IL2_modbus[2];

/*
///communication varibles for CAN Scope
int CT_CAN =0;
int CT_CAN_plot = 0;
tCANMsgObject sTXCANMessage;
unsigned char ucTXMsgData[8];
unsigned char *Ip, *Vp, *Dp, *Op;
unsigned int CAN_Vinfo;
unsigned int CAN_Iinfo;
unsigned int CAN_Dinfo;
unsigned int CAN_Oinfo;

///////////////////////   CAN Message for BMU  /////////////
// CAN message for the battery
tCANMsgObject sTXCANMessage_toBMU_310;
unsigned char ucTXMsgData_toBMU_310[8];

tCANMsgObject sRXCANMessage_fromBMU_043;
unsigned char ucRXMsgData_fromBMU_043[8];

tCANMsgObject sRXCANMessage_fromBMU_045;
unsigned char ucRXMsgData_fromBMU_045[8];

unsigned int CNT_CANtoBMU_120ms = 0;

///communication varibles for CAN Scope

unsigned char toBMU_310_byte2 = 0x0;  // 0x1 for closing the relay, 0x5 for closing the relay and balancing the cells
unsigned char toBMU_310_byte3 = 0x0;
unsigned char toBMU_310_byte4 = 0x0;
unsigned int fromBMU_043_byte67 = 0;
unsigned int fromBMU_045_byte8 = 0;
*/

//state machine
enum states_code { reset, initialization, operate, fault, shutdown};
enum states_code current_state, next_state;

int manual_ctrl = 0;
int start_stop = 0;
int fault_flg = 0;

float plot_array[84];
int plot_array_count = 0;
int plot_signal = 0;
int plot_array_i = 0;
float plot_array_sum = 0;
float plot_array_average = 0;
float test_gain = 0.1;
float voltage_test_gain = 1.8;
float droop_test_gain = 0.8;  // originally, it is 0.2
float w_incre = 0;
float Vmag_incre = 0;
int ini_to_op = 0;
float pi_out_i_d = 0;
float pi_out_i_q = 0;

float pi_out_v_d = 0;
float pi_out_v_q = 0;
void main(void) {
	
 	   InitSysCtrl();
	   InitCpuTimers(); //Initialize all CPU timers to known states


	  //Configure GPIO for RST, RDT, RELAY1, RELAY2, OVERTEMPERATURE, DE-SATURATION
	    ConfigureGPIO();

	  //Configure the ADC and power it up, for grid voltage, cap votlage and inductor current
	    ConfigureADC();

	  //configure PWM synchronously
	      EALLOW;
	      CpuSysRegs.PCLKCR2.bit.EPWM2 = 1;
	      CpuSysRegs.PCLKCR2.bit.EPWM6 = 1;
	      CpuSysRegs.PCLKCR2.bit.EPWM10 = 1;
	      EDIS;

	      EALLOW;
	      CpuSysRegs.PCLKCR0.bit.TBCLKSYNC = 0;
	      EDIS;
	      ConfigurePWM1 ();
	      ConfigurePWM2 ();
	      ConfigurePWM6 ();
	      ConfigurePWM10 ();

	      EALLOW;
	      CpuSysRegs.PCLKCR0.bit.TBCLKSYNC = 1;
	      EDIS;
	         ////////////////////

	   // configure CAN bus
	      //ConfigureCAN( );

	  //Setup the ADC for ePWM triggered conversions on channel 0
	      init_adc_conversion();

	  // set up the PR controller parameters
	  // Controller_init();

	  //Configure pins GPIO 14 and 15 for SCIB
	      InitScibGpio();

	  // initialize modbus
	      ModbusInit();



	  ////////////////////////////////////////////////////////////////////////////////////////////////////

	    // CANIntEnable(CANA_BASE, CAN_INT_MASTER | CAN_INT_ERROR | CAN_INT_STATUS);


	  ///////////////////////////////////////////////////////////////////////////////////////////////////



		   DINT;
		// Initialize PIE control registers to their default state.
		// The default state is all PIE interrupts disabled and flags
		// are cleared.
		// This function is found in the DSP2833x_PieCtrl.c file.

		   InitPieCtrl();

		// Disable CPU interrupts and clear all CPU interrupt flags:
		   IER = 0x0000;
		   IFR = 0x0000;

		// Initialize the PIE vector table with pointers to the shell Interrupt
		// Service Routines (ISR).
		// This will populate the entire table, even if the interrupt
		// is not used in this example.  This is useful for debug purposes.
		// The shell ISR routines are found in DSP2833x_DefaultIsr.c.
		// This function is found in DSP2833x_PieVect.c.
		   InitPieVectTable();

		// Interrupts that are used in this example are re-mapped to
		// ISR functions found within this file.
		   EALLOW;	// This is needed to write to EALLOW protected registers
		   PieVectTable.SCIB_TX_INT	    = &SciTxIsrHandler;
		   PieVectTable.SCIB_RX_INT 	= &SciRxIsrHandler;
		   PieVectTable.TIMER0_INT 		= &CpuTimer0IsrHandler;
		   PieVectTable.ADCB1_INT       = &adcb1_isr; //function for ADCA interrupt 1
	//	   PieVectTable.CANA0_INT	    = &canaISR;
		   EDIS;   // This is needed to disable write to EALLOW protected registers

		 // Copy time critical code and Flash setup code to RAM
		 // MemCopy(&RamfuncsLoadStart, &RamfuncsLoadEnd, &RamfuncsRunStart);

		  // Enable interrupts required for this example
		   PieCtrlRegs.PIECTRL.bit.ENPIE 	= 1;   // Enable the PIE block
		   PieCtrlRegs.PIEIER9.bit.INTx3	= 1;   // PIE Group 9, INT3 //SCIRXINTB_ISR
		   PieCtrlRegs.PIEIER9.bit.INTx4 	= 1;   // PIE Group 9, INT4 FOR SCIB TX
		   PieCtrlRegs.PIEIER1.bit.INTx7 	= 1;   // TINT0 in the PIE: Group 1 interrupt 7 for timer0
		   PieCtrlRegs.PIEIER1.bit.INTx2    = 1;   // PIE Group 1, INT1 for ADCb
	//	   PieCtrlRegs.PIEIER9.bit.INTx5    = 1;   // PIE Group 9, INT1 for canaISR

		   IER 	|= M_INT9; //SCI Tx, Rx ISR
		   IER 	|= M_INT1; //CPU Timer ISR


		  EINT;

		  //CANGlobalIntEnable(CANA_BASE, CAN_GLB_INT_CANINT0);

		  // initialize CAN
		  // CANcommunication_init();
	 for (;;)
	 {

		 if (ScibRegs.SCIRXST.bit.RXERROR == 1)
		 {
			 ScibRegs.SCICTL1.bit.SWRESET = 0;
			 ScibRegs.SCICTL1.bit.SWRESET = 1;
		 }

		 angularFrequency_modbus = anglefreq_droop;
		 voltageMag_modbus = Vmag_pll;
		 mP_modbus = Power_droop_ref;
		 reactivePower_modbus = Qower_abc_lpf;

		 ModbusPoll();


		 if (manual_ctrl == 0)
		 {
			 start_stop = Start_Stop_modbus;
//			 P_command  = Pcommand_modbus_float;
		 }

		 /*
		 if (CNT_CANtoBMU_120ms == 4500)
		 {
			 CANMessageGet(CANA_BASE, 3, &sRXCANMessage_fromBMU_043, true);
			 fromBMU_043_byte67 = ( int ) ucRXMsgData_fromBMU_043[6]+ (( int ) ucRXMsgData_fromBMU_043[5])*256;//unit voltage
			 Battery_voltage = fromBMU_043_byte67*0.1;
			 toBMU_310_byte3 = ucRXMsgData_fromBMU_043[5];
			 toBMU_310_byte4 = ucRXMsgData_fromBMU_043[6];

			 CANMessageGet(CANA_BASE, 4, &sRXCANMessage_fromBMU_045, true);
			 fromBMU_045_byte8  = ( int ) ucRXMsgData_fromBMU_045[7];// unit soc
			 battery_SOC = fromBMU_045_byte8;
			 ucTXMsgData_toBMU_310[2] = ucRXMsgData_fromBMU_043[5];
			 ucTXMsgData_toBMU_310[3] = ucRXMsgData_fromBMU_043[6];

		 }
			*/
		 current_state = next_state;
	 }

}



interrupt void adcb1_isr(void)
{



	adc_A[0]   = AdcaResultRegs.ADCRESULT0;
	adc_B[0]   = AdcbResultRegs.ADCRESULT0;
	adc_A[1]   = AdcaResultRegs.ADCRESULT1;
	adc_B[1]   = AdcbResultRegs.ADCRESULT1;
	adc_A[2]   = AdcaResultRegs.ADCRESULT2;
	adc_B[2]   = AdcbResultRegs.ADCRESULT2;
	adc_A[3]   = AdcaResultRegs.ADCRESULT3;
	adc_B[3]   = AdcbResultRegs.ADCRESULT3;
	adc_A[4]   = AdcaResultRegs.ADCRESULT4;
	adc_B[4]   = AdcbResultRegs.ADCRESULT4;
	adc_A[5]   = AdcaResultRegs.ADCRESULT5;
	adc_B[5]   = AdcbResultRegs.ADCRESULT5;


	//////////////////////////         for DG1 and DG2         /////////////////////////////

	if (adc_A[5] < 500)     // Mode (grid-tied or islanded)
		gridtie_mode = 0;
	else
		gridtie_mode = 1;


	Vcab = (adc_A[0] *3./4096-1.5)*500;
	Vcbc = (adc_B[0] *3./4096-1.5)*500;
	Vcca2 = (adc_A[1] *3./4096-1.5)*500;
	Vcca = (adc_B[4] *3./4096-1.5)*500;   // why B[4] though?

	Ifa = (adc_B[1] *3./4096-1.5)*1666.6667;
	Ifb = (adc_A[2] *3./4096-1.5)*1666.6667;
	Ifc = (adc_B[2] *3./4096-1.5)*1666.6667;

	Vgab = (adc_A[3] *3./4096-1.5)*500;
	Vgbc = (adc_B[3] *3./4096-1.5)*500;
	Vgca = (adc_A[4] *3./4096-1.5)*500;



	Vca = Vcab;
	Vcb = Vcbc;
    Vcc = Vcca;

	Vga = Vgab;
	Vgb = Vgbc;
    Vgc = Vgca;

/*
    //////////////////////////         for DG3         /////////////////////////////

	if (adc_B[2] < 500)
		gridtie_mode = 0;
	else
		gridtie_mode = 1;

	Vcab = (adc_A[0] *3./4096-1.5)*500;
	Vcbc = (adc_B[0] *3./4096-1.5)*500;
	Vcca2 = (adc_A[1] *3./4096-1.5)*500;
	Vcca = (adc_B[5] *3./4096-1.5)*500;

	Ifa = (adc_B[1] *3./4096-1.5)*1666.6667 + 8;
	Ifb = (adc_A[2] *3./4096-1.5)*1666.6667 + 8;
	Ifc = (adc_A[5] *3./4096-1.5)*1666.6667 + 8;

	Vgab = (adc_A[3] *3./4096-1.5)*500;
	Vgbc = (adc_B[3] *3./4096-1.5)*500;
	Vgca = (adc_A[4] *3./4096-1.5)*500;


	Vca = Vcab;
	Vcb = Vcbc;
    Vcc = Vcca;

	Vga = Vgab;
	Vgb = Vgbc;
    Vgc = Vgca;
*/

    ///////////////////////////   end of ADC v     /////////////////////////

	////////////////////////       begin of PLL     //////////////////////////////
	Vd_pll =  2/3.*(Vga*sin(phase_pll) + Vgb*sin(phase_pll - pi*2/3) + Vgc*sin(phase_pll + pi*2/3));
	Vq_pll =  2/3.*(Vga*cos(phase_pll) + Vgb*cos(phase_pll - pi*2/3) + Vgc*cos(phase_pll + pi*2/3));
	Vmag_pll = sqrt(Vq_pll*Vq_pll + Vd_pll*Vd_pll);
	Vq_pll = Vq_pll/Vmag_pll;

	anglefreq_pll = PI_Controller_PLL(-Vq_pll, 180, 3200 ,T10000Hz, 400, 0); // PI_Controller_PLL( float e, float Kp, float Ki, float T, float windup_limit, int reset)

	phase_pll = phase_pll + anglefreq_pll*T10000Hz;

	if (phase_pll >= 2*pi )
		phase_pll = phase_pll - 2*pi;
	else if (phase_pll < 0 )
		phase_pll = phase_pll + 2*pi;

	freq_pll = anglefreq_pll/2/pi;

	grid_voltage_is_OK = grid_voltage_is_locked(Vmag_pll, anglefreq_pll);
	////////////////////////       end of PLL     //////////////////////////////

	////////////////////////       begin of droop loop     /////////////////////////


	Power_abc = Vca*Ifa + Vcb*Ifb + Vcc*Ifc;
	Qower_abc = ((Vcb-Vcc)*Ifa + (Vcc-Vca)*Ifb + (Vca-Vcb)*Ifc)/sqrt(3);
	//Power_dq0 = 3./2*(Vd_cap*Id_fil + Vq_cap*Iq_fil);
	//Power_abc_lpf = Power_abc*0.05 + Power_abc_lpf* 0.95;
	Power_abc_lpf = Power_abc*0.01 + Power_abc_lpf* 0.99; //8Hz cut off frequency for 5000Hz Ts
	Qower_abc_lpf = Qower_abc*0.01 + Qower_abc_lpf* 0.99;
	//Power_dq0_lpf = Power_dq0*0.01 + Power_dq0_lpf* 0.99;

	 //reset, initialization, operate, fault, shutdown

	switch (current_state){

		 case reset :

			 next_state = current_state;

			 // trip all the swicthes
			 trip_all_switches();

			 // trip the relay
			 GpioDataRegs.GPASET.bit.GPIO20 = 0;
			 GpioDataRegs.GPACLEAR.bit.GPIO20 = 1;

			 //reset all the PI controllers
			 PI_Controller_Qower(0, 0, 0, 0, 0, 1);

			 PI_Controller_V1(0, 0, 0, 0, 0, 1)  ;
			 PI_Controller_V2(0, 0, 0, 0, 0, 1)  ;

			 PI_Controller_I1(0, 0, 0, 0, 0, 1)  ;
			 PI_Controller_I2(0, 0, 0, 0, 0, 1)  ;

			 // enter next state of PLL is locked
			 if (start_stop == 1 && grid_voltage_is_OK  && fault_flg == 0 )   //it will stay in reset state unless receiving start command and DC voltage is OK in power mode
				 {
				 	 next_state = initialization;
				 }

			 break;


		 case initialization :

			next_state = current_state;
			// untrip all the swicthes
			untrip_all_switches();
			// trip the relay
			GpioDataRegs.GPASET.bit.GPIO20 = 0;
			GpioDataRegs.GPACLEAR.bit.GPIO20 = 1;

			phase_pll_compensated = phase_pll + phase_compensation;
			phase_droop = phase_pll_compensated;

			Vd_cap_ref = Vd_pll ;
			Vq_cap_ref = Vq_pll ;

			Vd_cap =  2/3.*(Vca*sin(phase_pll_compensated) + Vcb*sin(phase_pll_compensated - pi*2/3) + Vcc*sin(phase_pll_compensated + pi*2/3));
			Vq_cap =  2/3.*(Vca*cos(phase_pll_compensated) + Vcb*cos(phase_pll_compensated - pi*2/3) + Vcc*cos(phase_pll_compensated + pi*2/3));

			Id_fil =  2/3.*(Ifa*sin(phase_pll_compensated) + Ifb*sin(phase_pll_compensated - pi*2/3) + Ifc*sin(phase_pll_compensated + pi*2/3));
			Iq_fil =  2/3.*(Ifa*cos(phase_pll_compensated) + Ifb*cos(phase_pll_compensated - pi*2/3) + Ifc*cos(phase_pll_compensated + pi*2/3));

			////////////////////////       begin of voltage loop     /////////////////////////

			// PI_Controller_V( float e, float Kp, float Ki, float T, float windup_limit, int reset)
			Id_fil_ref = PI_Controller_V1(Vd_cap_ref - Vd_cap, 2.7*voltage_test_gain, 700*voltage_test_gain, T10000Hz, 2500, 0) - wC*Vq_cap_ref ;
			Iq_fil_ref = PI_Controller_V2(Vq_cap_ref - Vq_cap,  2.7*voltage_test_gain, 700*voltage_test_gain, T10000Hz, 2500, 0) + wC*Vd_cap_ref ;

			////////////////////////       end of voltage loop     /////////////////////////

			////////////////////////       begin of current loop     /////////////////////////


			md = PI_Controller_I1(Id_fil_ref - Id_fil, 3.1*test_gain , 500*test_gain , T10000Hz, 12000, 0) + 2*Vd_cap - 2*wL*Iq_fil_ref;
			mq = PI_Controller_I2(Iq_fil_ref - Iq_fil, 3.1*test_gain , 500*test_gain , T10000Hz, 12000, 0) + 2*Vq_cap + 2*wL*Id_fil_ref;

			ma_unlimited = md * sin(phase_pll_compensated)          + mq * cos(phase_pll_compensated);
			mb_unlimited = md * sin(phase_pll_compensated - pi*2/3) + mq * cos(phase_pll_compensated - pi*2/3);
			mc_unlimited = md * sin(phase_pll_compensated + pi*2/3) + mq * cos(phase_pll_compensated + pi*2/3);

			ma_limited = M_clamp_ac(ma_unlimited / 1200);
			mb_limited = M_clamp_ac(mb_unlimited / 1200);
			mc_limited = M_clamp_ac(mc_unlimited / 1200);

			ma_limited = ma_limited*0.5 + 0.5;
			mb_limited = mb_limited*0.5 + 0.5;
			mc_limited = mc_limited*0.5 + 0.5;


			EPwm2Regs.CMPA.bit.CMPA  = 10000*ma_limited;
			EPwm6Regs.CMPA.bit.CMPA  = 10000*mb_limited;
			EPwm10Regs.CMPA.bit.CMPA = 10000*mc_limited;

	        Vc_is_Vg = cap_voltage_is_grid_voltage( Vd_cap, Vq_cap, Vd_pll, Vq_pll);


			if (start_stop == 0 )
			{
				next_state = shutdown;
			}


			else if ( cap_voltage_is_grid_voltage( Vd_cap, Vq_cap, Vd_pll, Vq_pll) && ini_to_op ==1 )
			{
				next_state = operate;
			}

			break;

		 case operate :

			 next_state = current_state;
			 // untrip all the swicthes
			 untrip_all_switches();
			 // trip the relay
			 GpioDataRegs.GPASET.bit.GPIO20 = 1;
			 GpioDataRegs.GPACLEAR.bit.GPIO20 = 0;

			 // w/P droop
			 w_incre = droop_test_gain*2*pi*(Power_droop_ref - Power_abc_lpf)/1000000.;
			 anglefreq_droop = w60Hz +w_incre;
/*
			 if (secondary_control_enable_modbus == 1)
				 own_secondary_variable = own_secondary_variable + (376.9912-anglefreq_pll)*0.01;
			 else
				own_secondary_variable = 0;
*/
			 if (secondary_control_enable_modbus == 1)
				 //anglefreq_droop = anglefreq_droop + own_secondary_variable;
			 	 anglefreq_droop = anglefreq_droop + omegaSecCtrl_modbus_float;

			 phase_droop = phase_droop + anglefreq_droop*T10000Hz;
			 if (phase_droop >= 2*pi )
			 	phase_droop = phase_droop - 2*pi;
			 else if (phase_droop < 0 )
			 	phase_droop = phase_droop + 2*pi;

			 // V/Q droop
			 if (gridtie_mode == 1) // This is just for debug purpose
			 //if (islanding_mode_modbus == 0)
			 {
				 Vmag_incre = - PI_Controller_Qower(Qower_droop_ref - Qower_abc_lpf, 0.0001, 0.001, T10000Hz, 200, 0);
			 	 Vmag_droop = -392 + Vmag_incre;
//Vmag_droop = -392;
				 GpioDataRegs.GPASET.bit.GPIO17 = 0;
				 GpioDataRegs.GPACLEAR.bit.GPIO17 = 1;
			 }
			 else
			 {
				 Vmag_incre = - 20*(Qower_droop_ref - Qower_abc_lpf)/200000.;
			 	 Vmag_droop = -392 + Vmag_incre ;
				 GpioDataRegs.GPASET.bit.GPIO17 = 1;
				 GpioDataRegs.GPACLEAR.bit.GPIO17 = 0;
			 }
			 if (secondary_control_enable_modbus == 1)
				 //Vmag_droop = Vmag_droop ;
			 	 Vmag_droop = Vmag_droop - eSecCtrl_modbus_float;

			 phase_pll_compensated = phase_droop;

			 // abc to dq transform
			 Vd_cap =  2/3.*(Vca*sin(phase_pll_compensated) + Vcb*sin(phase_pll_compensated - pi*2/3) + Vcc*sin(phase_pll_compensated + pi*2/3));
			 Vq_cap =  2/3.*(Vca*cos(phase_pll_compensated) + Vcb*cos(phase_pll_compensated - pi*2/3) + Vcc*cos(phase_pll_compensated + pi*2/3));

			 Id_fil =  2/3.*(Ifa*sin(phase_pll_compensated) + Ifb*sin(phase_pll_compensated - pi*2/3) + Ifc*sin(phase_pll_compensated + pi*2/3));
			 Iq_fil =  2/3.*(Ifa*cos(phase_pll_compensated) + Ifb*cos(phase_pll_compensated - pi*2/3) + Ifc*cos(phase_pll_compensated + pi*2/3));


			 // power in dq
			 Vd_cap_lpf =Vd_cap*0.2 + Vd_cap_lpf*0.8 ;
			 Vq_cap_lpf =Vq_cap*0.2 + Vq_cap_lpf*0.8 ;
			 Id_fil_lpf = Id_fil*0.1 + Id_fil_lpf*0.9;
			 Iq_fil_lpf = Iq_fil*0.1 + Iq_fil_lpf*0.9;

			 Power_dq = 3./2*(Vd_cap_lpf*Id_fil_lpf  + Vq_cap_lpf*Iq_fil_lpf);
			 Qower_dq = 3./2*(Vq_cap_lpf*Id_fil_lpf -  Vd_cap_lpf*Iq_fil_lpf);

			 Power_dq_lpf = Power_dq * 0.01 + Power_dq_lpf * 0.99;
			 Qower_dq_lpf = Qower_dq * 0.01 + Qower_dq_lpf * 0.99;
			 //virtual impedance
			 Vd_cap_ref = Vmag_droop - Rvirtual*Id_fil + w60Hz*Lvirtual*Iq_fil;
			 Vq_cap_ref = 0 - Rvirtual*Iq_fil - w60Hz*Lvirtual*Id_fil;



			 ////////////////////////       begin of voltage loop     /////////////////////////

			 // PI_Controller_V( float e, float Kp, float Ki, float T, float windup_limit, int reset)
			 pi_out_v_d = PI_Controller_V1(Vd_cap_ref - Vd_cap, 2.7*voltage_test_gain, 700*voltage_test_gain, T10000Hz, 2500, 0);
			 pi_out_v_q = PI_Controller_V2(Vq_cap_ref - Vq_cap, 2.7*voltage_test_gain, 700*voltage_test_gain, T10000Hz, 2500, 0);
			 Id_fil_ref = pi_out_v_d - wC*Vq_cap_ref ;
			 Iq_fil_ref = pi_out_v_q + wC*Vd_cap_ref ;

			 ////////////////////////       end of voltage loop     /////////////////////////

			 ////////////////////////       begin of current loop     /////////////////////////

			 pi_out_i_d = PI_Controller_I1(Id_fil_ref - Id_fil, 3.1*test_gain , 500*test_gain , T10000Hz, 12000, 0);
			 pi_out_i_q = PI_Controller_I2(Iq_fil_ref - Iq_fil, 3.1*test_gain , 500*test_gain , T10000Hz, 12000, 0);
			 md =  pi_out_i_d + 2*Vd_cap - 2*wL*Iq_fil_ref;
			 mq =  pi_out_i_q + 2*Vq_cap + 2*wL*Id_fil_ref;

			 ma_unlimited = md * sin(phase_pll_compensated)          + mq * cos(phase_pll_compensated);
			 mb_unlimited = md * sin(phase_pll_compensated - pi*2/3) + mq * cos(phase_pll_compensated - pi*2/3);
			 mc_unlimited = md * sin(phase_pll_compensated + pi*2/3) + mq * cos(phase_pll_compensated + pi*2/3);

			 ma_limited = M_clamp_ac(ma_unlimited / 1200);
			 mb_limited = M_clamp_ac(mb_unlimited / 1200);
			 mc_limited = M_clamp_ac(mc_unlimited / 1200);

			 ma_limited = ma_limited*0.5 + 0.5;
			 mb_limited = mb_limited*0.5 + 0.5;
			 mc_limited = mc_limited*0.5 + 0.5;

			 untrip_all_switches();

			 EPwm2Regs.CMPA.bit.CMPA  = 10000*ma_limited;
			 EPwm6Regs.CMPA.bit.CMPA  = 10000*mb_limited;
			 EPwm10Regs.CMPA.bit.CMPA = 10000*mc_limited;



			 if (start_stop == 0)
			 {
				next_state = shutdown;
			 }

			 break;

		 case fault :

			 //add fault case in the future

			 next_state = current_state;
			 break;

		 case shutdown :

		 	next_state = current_state;

		 	//add soft shutdown in the future

		 	trip_all_switches();
			GpioDataRegs.GPASET.bit.GPIO20 = 0;
			GpioDataRegs.GPACLEAR.bit.GPIO20 = 1;

			next_state = reset;

		 	break;

		 }

	GpioDataRegs.GPACLEAR.bit.GPIO21 = 1;

	if (LED_counter == 2500)
		GpioDataRegs.GPATOGGLE.bit.GPIO12 = 1;
	else if (LED_counter == 5000)
	{
		GpioDataRegs.GPATOGGLE.bit.GPIO13 = 1;
		LED_counter = 0;
	}
	LED_counter ++;
/*
	EPwm2Regs.CMPA.bit.CMPA  = 20000*0.5;
	EPwm6Regs.CMPA.bit.CMPA  = 20000*0.5;
	EPwm10Regs.CMPA.bit.CMPA = 20000*0.5;
*/
	if(plot_signal == 0)
		plot_array[plot_array_count] = Vcab;
	else if (plot_signal == 1)
		plot_array[plot_array_count] = Vcbc;
	else if (plot_signal == 2)
		plot_array[plot_array_count] = Vcca;
	else if (plot_signal == 3)
		plot_array[plot_array_count] = Ifa;
	else if (plot_signal == 4)
		plot_array[plot_array_count] = Ifb;
	else if (plot_signal == 5)
		plot_array[plot_array_count] = Ifc;
	else if (plot_signal == 6)
		plot_array[plot_array_count] = Vgab;
	else if (plot_signal == 7)
		plot_array[plot_array_count] = Vgbc;
	else if (plot_signal == 8)
		plot_array[plot_array_count] = Vgca;
	else if (plot_signal == 9)
		plot_array[plot_array_count] = Vd_pll;
	else if (plot_signal == 10)
		plot_array[plot_array_count] = Vq_pll;
	else if (plot_signal == 11)
		plot_array[plot_array_count] = anglefreq_pll;
	else if (plot_signal == 12)
		plot_array[plot_array_count] = phase_pll;
	else if (plot_signal == 13)
		plot_array[plot_array_count] = ma_limited;
	else if (plot_signal == 14)
		plot_array[plot_array_count] = mb_limited;
	else if (plot_signal == 15)
		plot_array[plot_array_count] = mc_limited;
	else if (plot_signal == 16)
		plot_array[plot_array_count] = Vcca2;
	else if (plot_signal == 17)
		plot_array[plot_array_count] = md;
	else if (plot_signal == 18)
		plot_array[plot_array_count] = mq;
	else if (plot_signal == 19)
		plot_array[plot_array_count] = Power_abc_lpf;
	else if (plot_signal == 20)
		plot_array[plot_array_count] = Qower_abc_lpf;
	else if (plot_signal == 21)
		plot_array[plot_array_count] = Vd_cap;
	else if (plot_signal == 22)
		plot_array[plot_array_count] = Vq_cap;
	else if (plot_signal == 23)
		plot_array[plot_array_count] = Id_fil;
	else if (plot_signal == 24)
		plot_array[plot_array_count] = Iq_fil;
	else if (plot_signal == 25)
		plot_array[plot_array_count] = Vd_cap_ref - Vd_cap;
	else if (plot_signal == 26)
		plot_array[plot_array_count] = Vq_cap_ref - Vq_cap;
	else if (plot_signal == 27)
		plot_array[plot_array_count] = Id_fil_ref - Id_fil;
	else if (plot_signal == 28)
		plot_array[plot_array_count] = Iq_fil_ref - Iq_fil;
	else if (plot_signal == 29)
		plot_array[plot_array_count] = ma_unlimited;
	else if (plot_signal == 30)
		plot_array[plot_array_count] = mb_unlimited;
	else if (plot_signal == 31)
		plot_array[plot_array_count] = mc_unlimited;
	else

		plot_array[plot_array_count] = 0;

	plot_array_count =  plot_array_count + 1;
	if (plot_array_count > 83)
		plot_array_count = 0;

	plot_array_sum = 0;
	for ( plot_array_i = 0 ; plot_array_i < 84; plot_array_i++)
		plot_array_sum = plot_array_sum + plot_array[plot_array_i];

	plot_array_average = plot_array_sum / 84;


//////////////////// State Machine ////////////////////
/*
	 //reset, initialization, operate, fault, shutdown

	 switch (current_state){

	 case reset :

		 next_state = current_state;

		 //uncomment this during close loop test
		 //trip_all_switches();

		 tripswitch_cnt = 0;

		 reset_all_relays();
		 relay_1and3_cnt = 0;
		 relay_2and4_cnt = 0;
		 P_ramp = 0;

		 PI_Controller_I2(0, 0, 0, dT, 1, 1);
		 PI_Controller_I1(0, 0, 0, dT, 1, 1);

		 if (start_stop == 1 && DC_voltage_is_OK(Vdc_mea) && fault_flg == 0 )   //it will stay in reset state unless receiving start command and DC voltage is OK in power mode
			 {
			 	 next_state = initialization;
			 }

		 break;


	 case initialization :

		 next_state = current_state;
		 set_battery_relay = 1;
		 trip_all_switches();

////////////////
		 // if relay is set, counter increases until it is set
		 if ( !relay_1and3_is_set() )
			 {
			 	 relay_1and3_cnt++;
			 }
		 if (relay_1and3_cnt >= 200000)
			 {
			 	 set_relay_1and3 ();
			 }
//////////////////
		 if ( !relay_2and4_is_set() )
			 {
			 	 relay_2and4_cnt++;
			 }

		 if ( relay_1and3_is_set() && battery_voltage_is_OK(Battery_voltage)  && relay_2and4_cnt >= 300000) //set relay 2 and 4 after 1 and 3 and the battery voltage is OK
			 {
			 	 set_relay_2and4 ();
			 }

		 if (!DC_voltage_is_OK(Vdc_mea)) //DC voltage goes wrong
		 	 {
		 			 next_state = fault; fault_state = 3;break;
		 	 }

//////////////////////////////////////
		 if ( battery_voltage_is_OK(Battery_voltage) && relay_1and3_is_set() && relay_2and4_is_set())  //if all relays are set and battery voltage is OK
			 {

			 	 if ( (P_command >= 0 && battery_SOC > 10) || (P_command <= 0 && battery_SOC < 90) ) // if SOC and power command will not overcharge and overdischarge
		 		 	 {
			 		 	 next_state = operate;
			 		 	 duty_offset = 1-Battery_voltage/Vdc_mea;
		 		 	 }
			 	 else  // avoid overchange or overdischarge
			 	 	 {
			 		 	 next_state = fault; fault_state =1; break;
			 	 	 }
			 }
		 else if ( !battery_voltage_is_OK(Battery_voltage)  && relay_1and3_is_set() && relay_2and4_is_set() ) // if relay is set but the battery voltage is not right
		 	 {
			 	 next_state = fault;fault_state = 2; break;
		 	 }

		 else
		 	 {
			 	 next_state = current_state;
		 	 }

////////////////////////////////////

		 if (start_stop == 0) //if stop command is received
		 	 {
			 	 	 next_state = reset;
		 	 }

		 break;

	 case operate :

		 next_state = current_state;

		 set_battery_relay = 1;
		 set_relay_1and3 ();
		 set_relay_2and4 ();


		 untrip_all_switches();

		 //here starts the control code, better to use functions to keep it short

		 Vdc_cap = Vdc[0];
	  	 I1_ind = IL1[0];
	  	 I2_ind = IL2[0];

	  	  /////////// Power Loop /////////////
	  	if( P_command > 2000 ) P_command = 2000;
	  	if( P_command < -2000 ) P_command = -2000;

	  	//if (P_ramp <= 500) P_ramp = 500;
	  	// P ramp generator//
	  	if (P_command - P_ramp >= 5) P_ramp = P_ramp + 5;
	  	else if (P_command - P_ramp <= -5 ) P_ramp = P_ramp - 5;

	  	if (battery_voltage_is_OK(Battery_voltage))
	  		Iind_ref = P_ramp/Battery_voltage;
	  	else
	  	{
	  		Iind_ref = 0;
	  		next_state = fault;  fault_state = 4; break;

	  	}

	  	if( Iind_ref > 20 ) Iind_ref = 20;
	  	if( Iind_ref < -20 ) Iind_ref = -20;

	  	 ///////////////  current PI controller  //////
	  	err_Iind1 = (Iind_ref/2) - I1_ind;
	  	mt_dc_b = PI_Controller_I1(err_Iind1, Kp_IL1, Ki_IL1, dT, 1, 0);
	  	mt_dc_b =  mt_dc_b + duty_offset;

	  	err_Iind2 = (Iind_ref/2) - I2_ind;
	    mt_dc_a = PI_Controller_I2(err_Iind2, Kp_IL2, Ki_IL2, dT, 1, 0);
	    mt_dc_a =  mt_dc_a + duty_offset;


	    mt_dc_PhA = M_clamp_dc(mt_dc_a);
        EPwm2Regs.CMPA.bit.CMPA = 1333*mt_dc_PhA;

	    mt_dc_PhB = M_clamp_dc(mt_dc_b);
        EPwm6Regs.CMPA.bit.CMPA = 1333*mt_dc_PhB;

		//end of control here


		 if (!DC_voltage_is_OK(Vdc_mea)  )  // if voltages go wrong
		 {
			 next_state = fault; fault_state = 5; break;
		 }

		 if ( !battery_voltage_is_OK(Battery_voltage))
		 {
			 next_state = fault; fault_state = 6; break;
		 }

		 if ( (P_command < 0 && battery_SOC > 90) || (P_command > 0 && battery_SOC < 10) ) // if SOC and power command will overcharge and overdischarge
		 {
		 	next_state = shutdown;
		 }

		 if (start_stop == 0) //if stop command is received
		 {
		 	next_state = shutdown;
		 }

		 break;

	 case fault :

		 next_state = current_state;

		 fault_flg = 1;
		 trip_all_switches();  // first trip the siwtches

		 // counter decreases while the relays are set
		 if ( relay_1and3_is_set() )
			 {
			 	 relay_1and3_cnt--;
			 }
		 //  trip relay after some time
		 if (relay_1and3_cnt < 2)
			 {
			 	 reset_relay_1and3 ();
			 }

		 if ( relay_2and4_is_set() )
			 {
			 	 relay_2and4_cnt--;
			 }
		 if ( relay_2and4_cnt <= 1 )
		 	{
		 		 reset_relay_2and4 ();
		 	}

		 // if relays are tripped, go to reset
		 if ( !relay_1and3_is_set() && !relay_2and4_is_set() )
		 {
			 set_battery_relay = 0;
			 next_state = reset;
		 }

	 case shutdown :

	 		next_state = current_state;

	 		// I ramp generator//
	 		P_command=0;

	 		Vdc_cap = Vdc[0];
	 		I1_ind = IL1[0];
	 	    I2_ind = IL2[0];

	 		/////////// Power Loop /////////////

	 	    // P ramp generator//
	 		if (P_command - P_ramp > 5) P_ramp = P_ramp + 5;
	 		else if (P_command - P_ramp < -5 ) P_ramp = P_ramp - 5;

	 		if (battery_voltage_is_OK(Battery_voltage))
	 			Iind_ref = P_ramp/Battery_voltage;
	 		else
	 			{
	 				Iind_ref = 0;
	 			  	next_state = fault;  fault_state = 7; break;
	 			}

	 		if( Iind_ref > 20 ) Iind_ref = 20;
	 		if( Iind_ref < -20 ) Iind_ref = -20;

	 		///////////////  current PI controller  //////
	 		err_Iind1 = (Iind_ref/2) - I1_ind;
	 		mt_dc_b = PI_Controller_I1(err_Iind1, Kp_IL1, Ki_IL1, dT, 1, 0);
	 		mt_dc_b =  mt_dc_b + duty_offset;

	 		err_Iind2 = (Iind_ref/2) - I2_ind;
	 		mt_dc_a = PI_Controller_I2(err_Iind2, Kp_IL2, Ki_IL2, dT, 1, 0);
	 		mt_dc_a =  mt_dc_a + duty_offset;


	 		mt_dc_PhA = M_clamp_dc(mt_dc_a);
	 		EPwm2Regs.CMPA.bit.CMPA = 1333*mt_dc_PhA;

	 		mt_dc_PhB = M_clamp_dc(mt_dc_b);
	 		EPwm6Regs.CMPA.bit.CMPA = 1333*mt_dc_PhB;
	 		//////////////////

	 		//First ramp down the current reference

	 		if ( abs(I1_ind) <= 2 &&  abs(I2_ind) <= 2 )
	 		{
	 			trip_all_switches();  // trip all the siwtches
	 		}

	 		 // counter decreases while the relays are set
	 		if ( relay_1and3_is_set() && software_trip_is_active() )
	 		{
	 			 	 relay_1and3_cnt--;
	 		}
	 		 //  trip relay after some time
	 		if ( relay_1and3_cnt < 2)
	 		{
	 			 	 reset_relay_1and3 ();
	 		}

	 		 if ( relay_2and4_is_set() && !relay_1and3_is_set() && software_trip_is_active()  )
	 			 {
	 			 	 relay_2and4_cnt--;
	 			 }
	 		 if ( relay_2and4_cnt <= 1 )
	 		 	{
	 		 		 reset_relay_2and4 ();
	 		 	}

	 		 // if relays are tripped, go to reset
	 		 if ( !relay_1and3_is_set() && !relay_2and4_is_set() && software_trip_is_active() )
	 		 {
	 			 next_state = reset;
	 		 }
	 		break;

	 } //end of switch clause
*/
	 ////////////////// CAN Communication /////////////////////////
/*
	if (CT_CAN == 24){

		CAN_Dinfo = floor(  (mt_dc_a)*65535 );
		CAN_Vinfo = floor(  (Vdc_mea+20)*65535/520 );
		CAN_Iinfo = floor(  (IL2_mea+5 )*65535/100 );
		CAN_Oinfo = floor(  (err_Iind2+40)*65535/80 );
		//test = (Iind_mea+50)*65535/100;
	    Dp = (unsigned char *) (&CAN_Dinfo);
	    Vp = (unsigned char *) (&CAN_Vinfo);
	    Ip = (unsigned char *) (&CAN_Iinfo);
	    Op = (unsigned char *) (&CAN_Oinfo);

	    ucTXMsgData[0] =  *(Dp) ;
	    ucTXMsgData[1] = ( *(Dp)>>8 ) ;

	    ucTXMsgData[2] = *(Vp) ;
	    ucTXMsgData[3] = *(Vp)>>8;

	    ucTXMsgData[4] = *(Ip) ;
	    ucTXMsgData[5] = *(Ip)>>8;

	    ucTXMsgData[6] = *(Op) ;
	    ucTXMsgData[7] = *(Op)>>8;

		CT_CAN = 0;
		CT_CAN_plot++;
		if(CT_CAN_plot>=30000) CT_CAN_plot = 0;
		CANMessageSet(CANA_BASE, 1, &sTXCANMessage, MSG_OBJ_TYPE_TX);
	 }
	CT_CAN++;

	 //following 4 lines are only for open loop test

	 if (set_battery_relay == 1) toBMU_310_byte2 = 0x5;
	 else toBMU_310_byte2 = 0x0;

	 //////////////// BMS Communication//////////////

	if (CNT_CANtoBMU_120ms == 9000){


		    ucTXMsgData_toBMU_310[0] = 0;
		    ucTXMsgData_toBMU_310[1] = toBMU_310_byte2;
		    ucTXMsgData_toBMU_310[2] = toBMU_310_byte3;
		    ucTXMsgData_toBMU_310[3] = toBMU_310_byte4;
		    ucTXMsgData_toBMU_310[4] = 0;
		    ucTXMsgData_toBMU_310[5] = 0;
		    ucTXMsgData_toBMU_310[6] = 0;
		    ucTXMsgData_toBMU_310[7] = 0;

		    CNT_CANtoBMU_120ms = 0;

			CANMessageSet(CANA_BASE, 2, &sTXCANMessage_toBMU_310, MSG_OBJ_TYPE_TX);
	}

	CNT_CANtoBMU_120ms++;
*/

	AdcbRegs.ADCINTFLGCLR.bit.ADCINT1 = 1; //clear INT1 flag
	PieCtrlRegs.PIEACK.all = PIEACK_GROUP1;

}

/*
__interrupt void canaISR(void)
{
    uint32_t status;

    //
    // Read the CAN-B interrupt status to find the cause of the interrupt
    //
    status = CANIntStatus(CANA_BASE, CAN_INT_STS_CAUSE);

    //
    // If the cause is a controller status interrupt, then get the status
    //
    if(status == CAN_INT_INT0ID_STATUS)
    {
        //
        // Read the controller status.  This will return a field of status
        // error bits that can indicate various errors.  Error processing
        // is not done in this example for simplicity.  Refer to the
        // API documentation for details about the error status bits.
        // The act of reading this status will clear the interrupt.
        //
        status = CANStatusGet(CANA_BASE, CAN_STS_CONTROL);

        //
        // Check to see if an error occurred.
        //
        if(((status  & ~(CAN_ES_RXOK)) != 7) &&
           ((status  & ~(CAN_ES_RXOK)) != 0))
        {
            //
            // Set a flag to indicate some errors may have occurred.
            //
      //      errorFlag = 1;
        }
    }
    //
    // Check if the cause is the CAN-B receive message object 1
    //
    else if(status == 3)
    {
        //
        // Get the received message
        //
        CANMessageGet(CANA_BASE, 3, &sRXCANMessage_fromBMU_043, true);
        fromBMU_340_byte67 = ( int ) ucRXMsgData_fromBMU_043[6]+ (( int ) ucRXMsgData_fromBMU_043[5])*256;
        //
        // Getting to this point means that the RX interrupt occurred on
        // message object 1, and the message RX is complete.  Clear the
        // message object interrupt.
        //
        CANIntClear(CANA_BASE, 3);

        //
        // Increment a counter to keep track of how many messages have been
        // received. In a real application this could be used to set flags to
        // indicate when a message is received.
        //
   //     rxMsgCount++;

        //
        // Since the message was received, clear any error flags.
        //
   //     errorFlag = 0;
    }
    //
    // If something unexpected caused the interrupt, this would handle it.
    //
    else
    {
        //
        // Spurious interrupt handling can go here.
        //
    }

    //
    // Clear the global interrupt flag for the CAN interrupt line
    //
    CANGlobalIntClear(CANA_BASE, CAN_GLB_INT_CANINT0);

    //
    // Acknowledge this interrupt located in group 9
    //
    PieCtrlRegs.PIEACK.all = PIEACK_GROUP9;
}
*/

/*

void Controller_init()
{

	VcapA[0] = 0;
	VcapA[1] = 0.000249933810255284;
	VcapA[2] = -0.000249933810255284;

	VcapB[0] = 1;
	VcapB[1] = -1.99941132139981;
	VcapB[2] = 0.999500124979169;

	IindA[0] = 0;
	IindA[1] = 0.000249933810255284;
	IindA[2] = -0.000249933810255284;

	IindB[0] = 1;
	IindB[1] = -1.99941132139981;
	IindB[2] = 0.999500124979169;

	A[0] = 0.981500789205860;
	A[1] = -1.96265287650335;
	A[2] = 0.981500789205860;

	B[1] = -1.96265287650335;
	B[2] = 0.963001578411720;

}

*/

/*
void CANcommunication_init()
{

	// CAN message for Scope
    sTXCANMessage.ui32MsgID = 1;                      // CAN message ID - use 1
    sTXCANMessage.ui32MsgIDMask = 0;                  // no mask needed for TX
    sTXCANMessage.ui32Flags = MSG_OBJ_TX_INT_ENABLE;  // enable interrupt on TX
    sTXCANMessage.ui32MsgLen = sizeof(ucTXMsgData);   // size of message is 8
    sTXCANMessage.pucMsgData = ucTXMsgData;           // ptr to message content

    // CAN message to BMU 310
    sTXCANMessage_toBMU_310.ui32MsgID = 0x310;                      // CAN message ID - use 1
    sTXCANMessage_toBMU_310.ui32MsgIDMask = 0;                  // no mask needed for TX
    sTXCANMessage_toBMU_310.ui32Flags = MSG_OBJ_TX_INT_ENABLE;  // enable interrupt on TX
    sTXCANMessage_toBMU_310.ui32MsgLen = sizeof(ucTXMsgData_toBMU_310);   // size of message is 8
    sTXCANMessage_toBMU_310.pucMsgData = ucTXMsgData_toBMU_310;           // ptr to message content

    *(unsigned long *)ucRXMsgData_fromBMU_043 = 0;
    *((unsigned long *)ucRXMsgData_fromBMU_043+1) = 0;
    sRXCANMessage_fromBMU_043.ui32MsgID = 0x043;                      // CAN message ID - use 1
    sRXCANMessage_fromBMU_043.ui32MsgIDMask = 0;                  // no mask needed for TX
    sRXCANMessage_fromBMU_043.ui32Flags = MSG_OBJ_NO_FLAGS;//MSG_OBJ_RX_INT_ENABLE;
    sRXCANMessage_fromBMU_043.ui32MsgLen = sizeof(ucRXMsgData_fromBMU_043);   // size of message is 4
    sRXCANMessage_fromBMU_043.pucMsgData = ucRXMsgData_fromBMU_043;           // ptr to message content
    CANMessageSet(CANA_BASE, 3, &sRXCANMessage_fromBMU_043, MSG_OBJ_TYPE_RX);

    *(unsigned long *)ucRXMsgData_fromBMU_045 = 0;
    *((unsigned long *)ucRXMsgData_fromBMU_045+1) = 0;
    sRXCANMessage_fromBMU_045.ui32MsgID = 0x045;                      // CAN message ID - use 1
    sRXCANMessage_fromBMU_045.ui32MsgIDMask = 0;                  // no mask needed for TX
    sRXCANMessage_fromBMU_045.ui32Flags = MSG_OBJ_NO_FLAGS;//MSG_OBJ_RX_INT_ENABLE;
    sRXCANMessage_fromBMU_045.ui32MsgLen = sizeof(ucRXMsgData_fromBMU_045);   // size of message is 4
    sRXCANMessage_fromBMU_045.pucMsgData = ucRXMsgData_fromBMU_045;           // ptr to message content
    CANMessageSet(CANA_BASE, 4, &sRXCANMessage_fromBMU_045, MSG_OBJ_TYPE_RX);

}*/
