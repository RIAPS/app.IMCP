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
#include "initial.h"
#define pi  3.141592653589793
#define Vbatt 120 //36
#define TWOPI 6.283185307179586
#define TWOPI_THIRD 2.094395102393195
#define TWO_THIRD 0.666666666666667
#define SWITCHING_FREQUENCY 10000
/*
// These are defined by the linker (see F28335.cmd)
extern Uint16 RamfuncsLoadStart;
extern Uint16 RamfuncsLoadEnd;
extern Uint16 RamfuncsRunStart;
*/
/*-------------------------------------------------------------------------*/

 /// globe variables
//float T5000Hz = 2e-4;
//float T10000Hz = 1e-4;
#if SWITCHING_FREQUENCY== 10000
	float	Tswitching = 1e-4;
	PWM_CNT_PERIOD = 10000;
	float power_filter_a =0.005;
	float power_filter_b =0.995; // 8 Hz at f = 10 kHz
	float heavy_power_filter_a =0.001;
	float heavy_power_filter_b =0.999; // 1 Hz at f = 10 kHz

	float plot_array[168];
	int plot_array_length = 168;
#else
	float	Tswitching = 2e-4;
	PWM_CNT_PERIOD = 20000;
	float power_filter_a =0.01;
	float power_filter_b =0.99;  // 8 Hz at f = 5 kHz
	float heavy_power_filter_a =0.002;
	float heavy_power_filter_b =0.998; // 1 Hz at f = 5 kHz

	float plot_array[84];
	int plot_array_length = 84;
#endif

#define w60Hz 376.9911184307752
float C_Cap = 800e-6;
float L_fil = 150e-6;

float wC = w60Hz * 800e-6;
float wL = w60Hz * 150e-6;

int gcb_control = 0;
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
// power variables

float Power_abc = 0;
float Qower_abc = 0;
float Power_abc_lpf = 0;
float Qower_abc_lpf = 0;
float Power_abc_heavey_lpf = 0;
float Qower_abc_heavey_lpf = 0;

float Power_dq = 0;
float Qower_dq = 0;
float Power_dq_lpf = 0;
float Qower_dq_lpf = 0;

#define Vmag_nominal 392  // this is a single phase peak voltage 480*sqrt(2)/sqrt(3)
float Vmag_setpoint = Vmag_nominal;
#define anglefreq_nominal w60Hz // 60 hz represented as angular frequency (376.9911184307752)
float anglefreq_setpoint = anglefreq_nominal;
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
float omegaSecCtrl_modbus_float;
float eSecCtrl_modbus_float;

	// commands for modbus holding registers
USHORT ControlWord_modbus;         // holding register 2000
float Pcommand_modbus;             // holding register 2001
float Qcommand_modbus;             // holding register 2002
float Vcommand_modbus;             // holding register 2003
float Fcommand_modbus;             // holding register 2004
float VQdroop_command_modbus;      // holding register 2005
float FPdroop_command_modbus;      // holding register 2006
float FaultAutoRstTime_modbus;     // holding register 2007

	// measurements for modbus input registers
float Ia_peak_modbus;     // Input register 0
float Ia_angle_modbus;    // Input register 1
float Ib_peak_modbus;     // Input register 2
float Ib_angle_modbus;    // Input register 3
float Ic_peak_modbus;     // Input register 4
float Ic_angle_modbus;    // Input register 5
float Ia_rms_modbus;      // Input register 6
float Ib_rms_modbus;      // Input register 7
float Ic_rms_modbus;      // Input register 8
float Va_rms_modbus;      // Input register 9
float Vb_rms_modbus;      // Input register 10
float Vc_rms_modbus;      // Input register 11
float Va_peak_modbus;     // Input register 12
float Va_angle_modbus;    // Input register 13
float Vb_peak_modbus;     // Input register 14
float Vb_angle_modbus;    // Input register 15
float Vc_peak_modbus;     // Input register 16
float Vc_angle_modbus;    // Input register 17
float activePower_modbus; // Input register 18
float reactivePower_modbus;     // Input register 19
float apparentPower_modbus;     // Input register 20
float powerFactor_modbus; // Input register 21
float frequency_modbus;    // Input register 22
float sync_freq_slip_modbus;     // Input register 23
float sync_volt_diff_modbus;     // Input register 24
float sync_ang_diff_modbus;      // Input register 25
USHORT status_modbus;  // Input register 26
//USHORT fault_status_modbus;  // Input register 27
float vref_modbus; // Input register 27
float wref_modbus; // Input register 28

float angularFrequency_modbus; //
float voltageMag_modbus;

float own_secondary_variable = 0;

//state machine
enum states_code { reset, initialization, operate, fault, shutdown};
enum states_code current_state, next_state;

int manual_ctrl = 0;
int start_stop = 0;
int vf_or_pq_mode = 0;
int fault_rst = 0;
int generator_run = 0;
int fault_flg = 0;

int Start_Stop_modbus = 0;
int islanding_mode = 0;
int secondary_control_enable_modbus = 0;



int plot_array_count = 0;
int plot_signal = 0;
int plot_array_i = 0;
float plot_array_sum = 0;
float plot_array_average = 0;
float test_gain = 0.1;
float voltage_test_gain = 1.8;
float droop_test_gain = 0.8;  // originally, it is 0.2
float w_incre = 0;
float w_incre_PI = 0;
float Vmag_incre = 0;
float Vmag_incre_PI = 0;




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

		 angularFrequency_modbus = 59.9911;

		 Ia_peak_modbus      = 0;     // Input register 0
		 Ia_angle_modbus     = 0;    // Input register 1
		 Ib_peak_modbus      = 0;     // Input register 2
		 Ib_angle_modbus     = 120;    // Input register 3
		 Ic_peak_modbus      = 0;     // Input register 4
		 Ic_angle_modbus     = -120;    // Input register 5
		 Ia_rms_modbus       = 0;      // Input register 6
		 Ib_rms_modbus       = 0;      // Input register 7
		 Ic_rms_modbus       = 0;      // Input register 8
		 Va_rms_modbus       = Vmag_pll/sqrt(2);      // Input register 9
		 Vb_rms_modbus       = Va_rms_modbus;      // Input register 10
		 Vc_rms_modbus       = Va_rms_modbus;      // Input register 11
		 Va_peak_modbus      = Vmag_pll;     // Input register 12
		 Va_angle_modbus     = 0;    // Input register 13
		 Vb_peak_modbus      = Vmag_pll;     // Input register 14
		 Vb_angle_modbus     = 120;    // Input register 15
		 Vc_peak_modbus      =  Vmag_pll;      // Input register 16
		 Vc_angle_modbus     = -120;    // Input register 17
		 activePower_modbus   = Power_abc_heavey_lpf/1000 - 10; // Input register 18
		 reactivePower_modbus = Qower_abc_heavey_lpf/1000;     // Input register 19
		 apparentPower_modbus = sqrt(activePower_modbus*activePower_modbus + reactivePower_modbus*reactivePower_modbus);     // Input register 20
		 powerFactor_modbus   = activePower_modbus/apparentPower_modbus; // Input register 21
		 frequency_modbus     = anglefreq_droop/TWOPI;    // Input register 22
		 sync_freq_slip_modbus = 0.1 ;     // Input register 23
		 sync_volt_diff_modbus = 14;     // Input register 24
		 sync_ang_diff_modbus  = 5 ;      // Input register 25
		 status_modbus         = 0 ;  // Input register 26
//		 fault_status_modbus   = 0 ;  // Input register 27
		 vref_modbus = (Vmag_setpoint - Vmag_incre_PI)/Vmag_nominal;  // Input register 27
		 wref_modbus =( anglefreq_setpoint  + w_incre_PI)/anglefreq_nominal;  // Input register 28

		 status_modbus = status_modbus + status_modbus;
		 status_modbus = status_modbus + 2 * (1-gcb_control);
		 status_modbus = status_modbus + 4 * (gcb_control);

		 ModbusPoll();


		 if (manual_ctrl == 0)
		 {
			 start_stop = ControlWord_modbus & 1;
			 vf_or_pq_mode    = ((ControlWord_modbus & 2)==2);    // 1 is vf mode and 0 is pq mode
			 fault_rst        = ((ControlWord_modbus & 4)==4);
			 generator_run    = ((ControlWord_modbus & 8)==8);

			 //Power_droop_ref    = Pcommand_modbus*1000;             // holding register 2001
			 //Qower_droop_ref    = Qcommand_modbus*1000;             // holding register 2002
			 //Vmag_setpoint      = Vcommand_modbus*1.414/1.732;             // holding register 2003
			 //anglefreq_setpoint =  Fcommand_modbus*TWOPI;             // holding register 2004
			 ///following three parameters not used for now
			 // VQdroop_command_modbus;      // holding register 2005
			 // FPdroop_command_modbus;      // holding register 2006
			 // FaultAutoRstTime_modbus;     // holding register 2007

			 // this is a hack, use mode signal to for island signal
			 // which means VF mode in islanded operation and PQ mode in grid-tied operation
			 // which means we could not use PQ mode in islanded operation
			 // and we could not use VF mode in grid-tied operation (this makes sense)
			 if (vf_or_pq_mode == 1){
				 islanding_mode = 1;}
			 else{
				 islanding_mode = 0;
			 }


			 Vmag_setpoint      =  Vcommand_modbus*1.414/1.732;
			 anglefreq_setpoint =  Fcommand_modbus*TWOPI;

			 Power_droop_ref    =  Pcommand_modbus*1000;
			 Qower_droop_ref    =  Qcommand_modbus*1000;

		 }
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


	//////////////////////////         for DG1, DG2, DG4        /////////////////////////////

	if (adc_A[5] < 500)     // Mode (grid-tied or islanded)
		gridtie_mode = 0;
	else
		gridtie_mode = 1;

	// 3ph inverter capacitor voltage, phase-ground
	Vcab = (adc_A[0] *3./4096-1.5)*500;
	Vcbc = (adc_B[0] *3./4096-1.5)*500;
	Vcca2 = (adc_A[1] *3./4096-1.5)*500;
	Vcca = (adc_B[4] *3./4096-1.5)*500;

	// 3ph inverter inductor current
	Ifa = (adc_B[1] *3./4096-1.5)*1000;
	Ifb = (adc_A[2] *3./4096-1.5)*1000;
	Ifc = (adc_B[2] *3./4096-1.5)*1000;

	// 3ph grid voltage, phase-ground
	Vgab = (adc_A[3] *3./4096-1.5)*500;
	Vgbc = (adc_B[3] *3./4096-1.5)*500;
	Vgca = (adc_A[4] *3./4096-1.5)*500;

	Vca = Vcab;
	Vcb = Vcbc;
    Vcc = Vcca;

	Vga = Vgab;
	Vgb = Vgbc;
    Vgc = Vgca;

    //////////////////////////         for DG3         /////////////////////////////
/*
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
	Vd_pll =  TWO_THIRD*(Vga*sin(phase_pll) + Vgb*sin(phase_pll - TWOPI_THIRD) + Vgc*sin(phase_pll + TWOPI_THIRD));
	Vq_pll =  TWO_THIRD*(Vga*cos(phase_pll) + Vgb*cos(phase_pll - TWOPI_THIRD) + Vgc*cos(phase_pll + TWOPI_THIRD));
	Vmag_pll = sqrt(Vq_pll*Vq_pll + Vd_pll*Vd_pll);
	Vq_pll = Vq_pll/Vmag_pll;

	anglefreq_pll = PI_Controller_PLL(-Vq_pll, 180, 3200 ,Tswitching, 400, 0); // PI_Controller_PLL( float e, float Kp, float Ki, float T, float windup_limit, int reset)

	phase_pll = phase_pll + anglefreq_pll*Tswitching;

	if (phase_pll >= TWOPI )
		phase_pll = phase_pll - TWOPI;
	else if (phase_pll < 0 )
		phase_pll = phase_pll + TWOPI;

	freq_pll = anglefreq_pll/2/pi;

	grid_voltage_is_OK = grid_voltage_is_locked(Vmag_pll, anglefreq_pll);
	////////////////////////       end of PLL     //////////////////////////////

    ////////////////////////       begin of power calculation     /////////////////////////
    Power_abc = Vca*Ifa + Vcb*Ifb + Vcc*Ifc;
    Qower_abc = ((Vcb-Vcc)*Ifa + (Vcc-Vca)*Ifb + (Vca-Vcb)*Ifc)/sqrt(3);
    //Power_dq0 = 3./2*(Vd_cap*Id_fil + Vq_cap*Iq_fil);
    Power_abc_lpf = Power_abc*power_filter_a + Power_abc_lpf* power_filter_b; //8Hz cut off frequency for 5000Hz Ts
    Qower_abc_lpf = Qower_abc*power_filter_a + Qower_abc_lpf* power_filter_b;
    Power_abc_heavey_lpf = Power_abc*heavy_power_filter_a +Power_abc_heavey_lpf*heavy_power_filter_b;
    Qower_abc_heavey_lpf = Qower_abc*heavy_power_filter_a +Qower_abc_heavey_lpf*heavy_power_filter_b;
    //Power_dq0_lpf = Power_dq0*0.01 + Power_dq0_lpf* 0.99;
    ////////////////////////       end of power calculation     /////////////////////////


	////////////////////////       begin of droop loop     /////////////////////////



	 //reset, initialization, operate, fault, shutdown

	switch (current_state){

		 case reset :

			 next_state = current_state;

			 // trip all the swicthes
			 trip_all_switches();

			 // trip the relay
			 gcb_control = 0;
			 GpioDataRegs.GPASET.bit.GPIO20 = 0;
			 GpioDataRegs.GPACLEAR.bit.GPIO20 = 1;

			 //reset the setpoints
			 Vmag_setpoint = 392;
			 anglefreq_setpoint = 376.9911184307752;  //376.9911184307752 is 60 hz

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
			gcb_control = 0;
			GpioDataRegs.GPASET.bit.GPIO20 = 0;
			GpioDataRegs.GPACLEAR.bit.GPIO20 = 1;

			phase_pll_compensated = phase_pll + phase_compensation;
			phase_droop = phase_pll_compensated;

			Vd_cap_ref = Vd_pll ;
			Vq_cap_ref = Vq_pll ;

			Vd_cap =  TWO_THIRD*(Vca*sin(phase_pll_compensated) + Vcb*sin(phase_pll_compensated - TWOPI_THIRD) + Vcc*sin(phase_pll_compensated + TWOPI_THIRD));
			Vq_cap =  TWO_THIRD*(Vca*cos(phase_pll_compensated) + Vcb*cos(phase_pll_compensated - TWOPI_THIRD) + Vcc*cos(phase_pll_compensated + TWOPI_THIRD));

			Id_fil =  TWO_THIRD*(Ifa*sin(phase_pll_compensated) + Ifb*sin(phase_pll_compensated - TWOPI_THIRD) + Ifc*sin(phase_pll_compensated + TWOPI_THIRD));
			Iq_fil =  TWO_THIRD*(Ifa*cos(phase_pll_compensated) + Ifb*cos(phase_pll_compensated - TWOPI_THIRD) + Ifc*cos(phase_pll_compensated + TWOPI_THIRD));

			////////////////////////       begin of voltage loop     /////////////////////////

			// PI_Controller_V( float e, float Kp, float Ki, float T, float windup_limit, int reset)
			Id_fil_ref = PI_Controller_V1(Vd_cap_ref - Vd_cap, 2.7*voltage_test_gain, 700*voltage_test_gain, Tswitching, 2500, 0) - wC*Vq_cap_ref ;
			Iq_fil_ref = PI_Controller_V2(Vq_cap_ref - Vq_cap,  2.7*voltage_test_gain, 700*voltage_test_gain, Tswitching, 2500, 0) + wC*Vd_cap_ref ;

			////////////////////////       end of voltage loop     /////////////////////////

			////////////////////////       begin of current loop     /////////////////////////


			md = PI_Controller_I1(Id_fil_ref - Id_fil, 3.1*test_gain, 500*test_gain, Tswitching, 12000, 0) + Vd_cap - wL*Iq_fil_ref;
			mq = PI_Controller_I2(Iq_fil_ref - Iq_fil, 3.1*test_gain, 500*test_gain, Tswitching, 12000, 0) + Vq_cap + wL*Id_fil_ref;

            ////////////////////////       end of current loop     /////////////////////////

			ma_unlimited = md * sin(phase_pll_compensated)          + mq * cos(phase_pll_compensated);
			mb_unlimited = md * sin(phase_pll_compensated - TWOPI_THIRD) + mq * cos(phase_pll_compensated - TWOPI_THIRD);
			mc_unlimited = md * sin(phase_pll_compensated + TWOPI_THIRD) + mq * cos(phase_pll_compensated + TWOPI_THIRD);

			ma_limited = M_clamp_ac(ma_unlimited / 1200);
			mb_limited = M_clamp_ac(mb_unlimited / 1200);
			mc_limited = M_clamp_ac(mc_unlimited / 1200);

			ma_limited = ma_limited*0.5 + 0.5;
			mb_limited = mb_limited*0.5 + 0.5;
			mc_limited = mc_limited*0.5 + 0.5;


			EPwm2Regs.CMPA.bit.CMPA  = PWM_CNT_PERIOD*ma_limited;
			EPwm6Regs.CMPA.bit.CMPA  = PWM_CNT_PERIOD*mb_limited;
			EPwm10Regs.CMPA.bit.CMPA = PWM_CNT_PERIOD*mc_limited;



			if (start_stop == 0 )
			{
				next_state = shutdown;
			}

			else if ( cap_voltage_is_grid_voltage( Vd_cap, Vq_cap, Vd_pll, Vq_pll) )
			{
				next_state = operate;
			}

			break;

		 case operate :

			 next_state = current_state;
			 // untrip all the swicthes
			 untrip_all_switches();

			 // close the relay
			 gcb_control = 1;
			 GpioDataRegs.GPASET.bit.GPIO20 = 1;
			 GpioDataRegs.GPACLEAR.bit.GPIO20 = 0;


			 // this is added to the droop equation to guarantee accurate active power tracking when grid frequency is not 60Hz
			 if (islanding_mode == 0)
	             w_incre_PI = PI_Controller_Power( Power_droop_ref - Power_abc_lpf, 0.0, 0.00001, Tswitching, 6.28, 0.0);
             else
                 w_incre_PI = 0.0;


			 // w/P droop
			 w_incre = droop_test_gain*2*pi*(Power_droop_ref - Power_abc_lpf)/1000000.;
			 anglefreq_droop = anglefreq_setpoint + w_incre + w_incre_PI;




			 phase_droop = phase_droop + anglefreq_droop*Tswitching;
			 if (phase_droop >= TWOPI )
			 	phase_droop = phase_droop - TWOPI;
			 else if (phase_droop < 0 )
			 	phase_droop = phase_droop + TWOPI;

			 // V/Q droop
			 //if (gridtie_mode == 1)
			 if (islanding_mode == 0)
			 {
				 Vmag_incre_PI = - PI_Controller_Qower(Qower_droop_ref - Qower_abc_lpf, 0.0, 0.001, Tswitching, 100, 0);
				 Vmag_incre = - 20*(Qower_droop_ref - Qower_abc_lpf)/200000.;
			 	 Vmag_droop = -Vmag_setpoint + Vmag_incre+Vmag_incre_PI;
				 GpioDataRegs.GPASET.bit.GPIO17 = 0;
				 GpioDataRegs.GPACLEAR.bit.GPIO17 = 1;
			 }
			 else
			 {
				 Vmag_incre = - 20*(Qower_droop_ref - Qower_abc_lpf)/200000.;
			 	 Vmag_droop = -Vmag_setpoint + Vmag_incre ;   // Increase the voltage setpoint in islanded mode
				 GpioDataRegs.GPASET.bit.GPIO17 = 1;
				 GpioDataRegs.GPACLEAR.bit.GPIO17 = 0;
			 }


			 phase_pll_compensated = phase_droop;

			 // abc to dq transform
			 Vd_cap =  TWO_THIRD*(Vca*sin(phase_pll_compensated) + Vcb*sin(phase_pll_compensated - TWOPI_THIRD) + Vcc*sin(phase_pll_compensated + TWOPI_THIRD));
			 Vq_cap =  TWO_THIRD*(Vca*cos(phase_pll_compensated) + Vcb*cos(phase_pll_compensated - TWOPI_THIRD) + Vcc*cos(phase_pll_compensated + TWOPI_THIRD));

			 Id_fil =  TWO_THIRD*(Ifa*sin(phase_pll_compensated) + Ifb*sin(phase_pll_compensated - TWOPI_THIRD) + Ifc*sin(phase_pll_compensated + TWOPI_THIRD));
			 Iq_fil =  TWO_THIRD*(Ifa*cos(phase_pll_compensated) + Ifb*cos(phase_pll_compensated - TWOPI_THIRD) + Ifc*cos(phase_pll_compensated + TWOPI_THIRD));


			 // power calculation in dq
			 Vd_cap_lpf =Vd_cap*0.2 + Vd_cap_lpf*0.8 ;
			 Vq_cap_lpf =Vq_cap*0.2 + Vq_cap_lpf*0.8 ;
			 Id_fil_lpf = Id_fil*0.1 + Id_fil_lpf*0.9;
			 Iq_fil_lpf = Iq_fil*0.1 + Iq_fil_lpf*0.9;

			 Power_dq = 3./2*(Vd_cap_lpf*Id_fil_lpf  + Vq_cap_lpf*Iq_fil_lpf);
			 Qower_dq = 3./2*(Vq_cap_lpf*Id_fil_lpf -  Vd_cap_lpf*Iq_fil_lpf);

			 Power_dq_lpf = Power_dq * power_filter_a + Power_dq_lpf * power_filter_b;
			 Qower_dq_lpf = Qower_dq * power_filter_a + Qower_dq_lpf * power_filter_b;

			 //virtual impedance
			 Vd_cap_ref = Vmag_droop - Rvirtual*Id_fil + w60Hz*Lvirtual*Iq_fil;
			 Vq_cap_ref = 0 - Rvirtual*Iq_fil - w60Hz*Lvirtual*Id_fil;



			 ////////////////////////       begin of voltage loop     /////////////////////////

			 // PI_Controller_V( float e, float Kp, float Ki, float T, float windup_limit, int reset)
			 Id_fil_ref = PI_Controller_V1(Vd_cap_ref - Vd_cap, 2.7*voltage_test_gain, 700*voltage_test_gain, Tswitching, 2500, 0) - wC*Vq_cap_ref ;
			 Iq_fil_ref = PI_Controller_V2(Vq_cap_ref - Vq_cap, 2.7*voltage_test_gain, 700*voltage_test_gain, Tswitching, 2500, 0) + wC*Vd_cap_ref ;

			 ////////////////////////       end of voltage loop     /////////////////////////

			 ////////////////////////       begin of current loop     /////////////////////////

			 md = PI_Controller_I1(Id_fil_ref - Id_fil, 3.1*test_gain, 500*test_gain, Tswitching, 12000, 0) + Vd_cap - wL*Iq_fil_ref;
			 mq = PI_Controller_I2(Iq_fil_ref - Iq_fil, 3.1*test_gain, 500*test_gain, Tswitching, 12000, 0) + Vq_cap + wL*Id_fil_ref;
	            ////////////////////////       end of current loop     /////////////////////////

			 ma_unlimited = md * sin(phase_pll_compensated)          + mq * cos(phase_pll_compensated);
			 mb_unlimited = md * sin(phase_pll_compensated - TWOPI_THIRD) + mq * cos(phase_pll_compensated - TWOPI_THIRD);
			 mc_unlimited = md * sin(phase_pll_compensated + TWOPI_THIRD) + mq * cos(phase_pll_compensated + TWOPI_THIRD);

			 ma_limited = M_clamp_ac(ma_unlimited / 1200);
			 mb_limited = M_clamp_ac(mb_unlimited / 1200);
			 mc_limited = M_clamp_ac(mc_unlimited / 1200);

			 ma_limited = ma_limited*0.5 + 0.5;
			 mb_limited = mb_limited*0.5 + 0.5;
			 mc_limited = mc_limited*0.5 + 0.5;

			 untrip_all_switches();

			 EPwm2Regs.CMPA.bit.CMPA  = PWM_CNT_PERIOD*ma_limited;
			 EPwm6Regs.CMPA.bit.CMPA  = PWM_CNT_PERIOD*mb_limited;
			 EPwm10Regs.CMPA.bit.CMPA = PWM_CNT_PERIOD*mc_limited;



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
			gcb_control = 0;
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
		plot_array[plot_array_count] = Power_abc;
	else if (plot_signal == 18)
		plot_array[plot_array_count] = Qower_abc;
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
		plot_array[plot_array_count] = Power_abc_heavey_lpf;
	else if (plot_signal == 26)
		plot_array[plot_array_count] = Qower_abc_heavey_lpf;
	else

		plot_array[plot_array_count] = 0;

	plot_array_count =  plot_array_count + 1;
	if (plot_array_count >= plot_array_length)
		plot_array_count = 0;

	plot_array_sum = 0;
	for ( plot_array_i = 0 ; plot_array_i < plot_array_length; plot_array_i++)
		plot_array_sum = plot_array_sum + plot_array[plot_array_i];

	plot_array_average = plot_array_sum / plot_array_length;

	AdcbRegs.ADCINTFLGCLR.bit.ADCINT1 = 1; //clear INT1 flag
	PieCtrlRegs.PIEACK.all = PIEACK_GROUP1;

}
