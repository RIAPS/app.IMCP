/*
 * initial.h
 *
 *  Created on: Jul 10, 2016
 *      Author: htu
 */

#ifndef INITIAL_H_
#define INITIAL_H_



#endif /* INITIAL_H_ */

int PWM_CNT_PERIOD;
void InitScibGpio(void);
void ConfigureADC(void);
void ConfigurePWM2(void);
void ConfigurePWM6(void);
void ConfigurePWM10(void);
void ConfigureGPIO(void);
void init_adc_conversion(void);
interrupt void adcb1_isr(void);
__interrupt void canaISR(void);
void Controller_init(void);
void CANcommunication_init(void);
void ConfigureCAN(void);
float PI_Controller_PLL( float e, float Kp, float Ki, float T, float windup_limit, int reset);
float PI_Controller_Qower( float e, float Kp, float Ki, float T, float windup_limit, int reset);
float PI_Controller_V1( float e, float Kp, float Ki, float T, float windup_limit, int reset);
float PI_Controller_V2( float e, float Kp, float Ki, float T, float windup_limit, int reset);
float PI_Controller_I1( float e, float Kp, float Ki, float T, float windup_limit, int reset);
float PI_Controller_I2( float e, float Kp, float Ki, float T, float windup_limit, int reset);
float M_clamp_ac( float M );
float M_clamp_dc( float M );
int DC_voltage_is_OK(float DC_voltage);        // check the DC voltage is within the( DCmin,DCmax). if yes, return 1; if no, return zero
int battery_voltage_is_OK(float Battery_voltage);   // check the battery voltage is within the( batterymin,batterymax). if yes, return 1; if no, return zero
void trip_all_switches(void);	   // trip all the swicthes in software way
void untrip_all_switches(void);    // untrip all the siwtches
int software_trip_is_active(void); //check the force trip function activity from the Trip Zone flag register
void reset_all_relays(void);	   // trip all the relays
void reset_relay_1and3 (void);	   // trip all the relay 1 and 3
void reset_relay_2and4 (void);	   // trip all the relay 2 and 4
void set_relay_1and3 (void);	   // turn on all the relay 1 and 3
void set_relay_2and4 (void);	   // turn on all the relay 2 and 4
int relay_1and3_is_set(void);	   // check the relay status from the GPIO data registers
int relay_2and4_is_set(void);      // check the relay status from the GPIO data registers
int grid_voltage_is_locked(float Vac_mag, float w);    //check if the grid voltage is locked;
int cap_voltage_is_grid_voltage(float cap_votlage_d, float cap_votlage_q, float grid_voltage_d, float grid_voltage_q);   //check if cap voltage is controlled the same as grid voltage
/*  extern int Relay_Test1;
	extern int Relay_Test2;
	extern int Relay_Test3;
	extern int Relay_Test4;
*/

//Write ADC configurations and power up the ADC for both ADC A and ADC B
void ConfigureADC(void)
{
	EALLOW;

	//write configurations
	AdcaRegs.ADCCTL2.bit.PRESCALE = 2; //set ADCCLK divider to /4
	AdcSetMode(ADC_ADCA, ADC_RESOLUTION_12BIT, ADC_SIGNALMODE_SINGLE);

	//Set pulse positions to late
	AdcaRegs.ADCCTL1.bit.INTPULSEPOS = 1;

	//power up the ADC
	AdcaRegs.ADCCTL1.bit.ADCPWDNZ = 1;

	//write configurations
	AdcbRegs.ADCCTL2.bit.PRESCALE = 2; //set ADCCLK divider to /4
	AdcSetMode(ADC_ADCB, ADC_RESOLUTION_12BIT, ADC_SIGNALMODE_SINGLE);

	//Set pulse positions to late
	AdcbRegs.ADCCTL1.bit.INTPULSEPOS = 1;

	//power up the ADC
	AdcbRegs.ADCCTL1.bit.ADCPWDNZ = 1;

	//delay for 1ms to allow ADC time to power up
	//DELAY_US(1000);

	EDIS;
}

void ConfigureGPIO(void)
{
	EALLOW;
/*
	//for pulse signal from BBB
	GpioCtrlRegs.GPBMUX2.bit.GPIO58 = 0;  	//  use as GPIO
	GpioCtrlRegs.GPBDIR.bit.GPIO58 = 0; 	//  use as INPUT
	GpioCtrlRegs.GPBPUD.bit.GPIO58 = 1;     // dsiable pull-up on GPIO58
	GpioCtrlRegs.GPBQSEL2.bit.GPIO58 = 3;   // Asynch input GPIO63
	InputXbarRegs.INPUT5SELECT = 58;
*/

		//for pulse signal from BBB
	GpioCtrlRegs.GPCMUX1.bit.GPIO78 = 0;  	//  use as GPIO
	GpioCtrlRegs.GPCDIR.bit.GPIO78 = 0; 	//  use as INPUT
	GpioCtrlRegs.GPCPUD.bit.GPIO78 = 1;     // dsiable pull-up on GPIO78 (TZ1)
	GpioCtrlRegs.GPCQSEL1.bit.GPIO78 = 3;   // Asynch input GPIO78
	InputXbarRegs.INPUT5SELECT = 78;


	//For led D9
	GpioCtrlRegs.GPAMUX1.bit.GPIO12 = 0;
	GpioCtrlRegs.GPADIR.bit.GPIO12 = 1;
	GpioCtrlRegs.GPAPUD.bit.GPIO12= 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPACLEAR.bit.GPIO12 = 1; 	//clear to restart;

	//For led D10
	GpioCtrlRegs.GPAMUX1.bit.GPIO13 = 0;
	GpioCtrlRegs.GPADIR.bit.GPIO13 = 1;
	GpioCtrlRegs.GPAPUD.bit.GPIO13 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPACLEAR.bit.GPIO13 = 1; 	//clear to restart;

	// for GPIO17
	GpioCtrlRegs.GPAMUX2.bit.GPIO17 = 0;
	GpioCtrlRegs.GPADIR.bit.GPIO17 = 1;
	GpioCtrlRegs.GPAPUD.bit.GPIO17= 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPACLEAR.bit.GPIO17 = 1; 	//clear to restart;

	// for GPIO20
	GpioCtrlRegs.GPAMUX2.bit.GPIO20 = 0;
	GpioCtrlRegs.GPADIR.bit.GPIO20 = 1;
	GpioCtrlRegs.GPAPUD.bit.GPIO20= 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPACLEAR.bit.GPIO20 = 1; 	//clear to restart;

	// for GPIO21
	GpioCtrlRegs.GPAMUX2.bit.GPIO21 = 0;
	GpioCtrlRegs.GPADIR.bit.GPIO21 = 1;
	GpioCtrlRegs.GPAPUD.bit.GPIO21= 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPACLEAR.bit.GPIO21 = 1; 	//clear to restart;

	// for relay A1 new power board
	GpioCtrlRegs.GPBMUX1.bit.GPIO41 = 0;
	GpioCtrlRegs.GPBDIR.bit.GPIO41 = 1;
	GpioCtrlRegs.GPBPUD.bit.GPIO41 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPBCLEAR.bit.GPIO41 = 1; 	//clear to restart;

	// for relay A2 new power board
	GpioCtrlRegs.GPBMUX2.bit.GPIO61 = 0;
	GpioCtrlRegs.GPBDIR.bit.GPIO61 = 1;
	GpioCtrlRegs.GPBPUD.bit.GPIO61 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPBCLEAR.bit.GPIO61 = 1; 	//clear to restart;

	// for relay B1 new power board
	GpioCtrlRegs.GPCMUX1.bit.GPIO65 = 0;
	GpioCtrlRegs.GPCDIR.bit.GPIO65 = 1;
	GpioCtrlRegs.GPCPUD.bit.GPIO65 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPCCLEAR.bit.GPIO65 = 1; 	//clear to restart;

	// for relay B2 new power board
	GpioCtrlRegs.GPCMUX1.bit.GPIO69 = 0;
	GpioCtrlRegs.GPCDIR.bit.GPIO69 = 1;
	GpioCtrlRegs.GPCPUD.bit.GPIO69 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPCCLEAR.bit.GPIO69 = 1; 	//clear to restart;

////////////////////////////////////////////////////////////////////////////////////////////////////////////
	//GPIO91 /RST signal
	GpioCtrlRegs.GPCMUX2.bit.GPIO91 = 0;
	GpioCtrlRegs.GPCDIR.bit.GPIO91 = 1;
	GpioCtrlRegs.GPCPUD.bit.GPIO91 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPCCLEAR.bit.GPIO91 = 1; 	//clear to restart;

	//GPIO87 relay1 signal
	GpioCtrlRegs.GPCMUX2.bit.GPIO86 = 0;
	GpioCtrlRegs.GPCDIR.bit.GPIO86 = 1;
	GpioCtrlRegs.GPCPUD.bit.GPIO86 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPCCLEAR.bit.GPIO86 = 1; 	//clear to restart;

	//
	//GPIO90 relay2 signal for the DC side
	GpioCtrlRegs.GPCMUX2.bit.GPIO90 = 0;
	GpioCtrlRegs.GPCDIR.bit.GPIO90 = 1;
	GpioCtrlRegs.GPCPUD.bit.GPIO90 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPCCLEAR.bit.GPIO90 = 1; 	//clear to restart;

	//GPIO87 relay2 signal
	GpioCtrlRegs.GPCMUX2.bit.GPIO87 = 0;
	GpioCtrlRegs.GPCDIR.bit.GPIO87 = 1;
	GpioCtrlRegs.GPCPUD.bit.GPIO87 = 1;  	//1 DISABLE since the gate drive has one
	GpioDataRegs.GPCCLEAR.bit.GPIO87 = 1; 	//clear to restart;

	//trip zone RDT
	GpioCtrlRegs.GPCPUD.bit.GPIO78 = 0;    // Enable pull-up on GPIO78 (TZ1)
	GpioCtrlRegs.GPCQSEL1.bit.GPIO78 = 3;  // Asynch input GPIO78 (TZ1)
	InputXbarRegs.INPUT1SELECT = 78;

	//trip zone desaturation
	GpioCtrlRegs.GPCPUD.bit.GPIO73 = 0;    // Enable pull-up on GPIO73 (TZ1)
	GpioCtrlRegs.GPCQSEL1.bit.GPIO73 = 3;  // Asynch input GPIO73 (TZ1)
	InputXbarRegs.INPUT2SELECT = 73;

	//trip zone overtemperature
	GpioCtrlRegs.GPBPUD.bit.GPIO63 = 0;    // Enable pull-up on GPIO63 (TZ1)
	GpioCtrlRegs.GPBQSEL2.bit.GPIO63 = 3;  // Asynch input GPIO63 (TZ1)
	InputXbarRegs.INPUT3SELECT = 63;

	EDIS;
}


void ConfigurePWM1(void)
{

	EALLOW;

		ClkCfgRegs.PERCLKDIVSEL.bit.EPWMCLKDIV= 0; //configure the PWM clock the same as system clock
		GpioCtrlRegs.GPAMUX1.bit.GPIO0 = 1;
		GpioCtrlRegs.GPAMUX1.bit.GPIO1 = 1;

		EPwm1Regs.TBCTL.bit.CLKDIV = 0;
		EPwm1Regs.TBCTL.bit.HSPCLKDIV = 0;
		EPwm1Regs.TBCTL.bit.CTRMODE = TB_COUNT_UPDOWN;           //upper and down mode
		EPwm1Regs.TBPRD = PWM_CNT_PERIOD;           // FOR 75KHz with 200MHz TB frequency for UP-DOWN mode

		EPwm1Regs.TBCTL.bit.SYNCOSEL = 0; //0 for external sync signal

		EPwm1Regs.CMPCTL.bit.SHDWAMODE = 0;  //shadow compare register
		EPwm1Regs.CMPCTL.bit.LOADAMODE = 0;  //load when CTR = 0;

		EPwm1Regs.CMPA.bit.CMPA = 0;    //duty cycle
		EPwm1Regs.CMPB.bit.CMPB = EPwm2Regs.CMPA.bit.CMPA ;     // duty cycle

		EPwm1Regs.AQCTLA.bit.CAD = AQ_SET;
		EPwm1Regs.AQCTLA.bit.CAU = AQ_CLEAR;
		//EPwm2Regs.AQCTLA.bit.PRD = 1;


		EPwm1Regs.DBCTL.bit.IN_MODE = 0; 	//COMA result is transferred to DB
		EPwm1Regs.DBCTL.bit.POLSEL = DB_ACTV_HIC;//2;
		EPwm1Regs.DBCTL.bit.OUT_MODE = 3;
		EPwm1Regs.DBRED.bit.DBRED = 50;
		EPwm1Regs.DBFED.bit.DBFED = 50;
/*

		// Assumes ePWM clock is already enabled
		EPwm2Regs.ETSEL.bit.SOCAEN	= 1;	        // Disable SOC on A group
		EPwm2Regs.ETSEL.bit.SOCASEL	= 1;	        // Select SOC on counter = 0
		EPwm2Regs.ETPS.bit.SOCAPRD = 1;		        // Generate pulse on 1st event
*/
	EDIS;
}


void ConfigurePWM2(void)
{

	EALLOW;

		ClkCfgRegs.PERCLKDIVSEL.bit.EPWMCLKDIV= 0; //configure the PWM clock the same as system clock
		GpioCtrlRegs.GPAMUX1.bit.GPIO2 = 1;
		GpioCtrlRegs.GPAMUX1.bit.GPIO3 = 1;

		EPwm2Regs.TBCTL.bit.CLKDIV = 0;
		EPwm2Regs.TBCTL.bit.HSPCLKDIV = 0;
		EPwm2Regs.TBCTL.bit.CTRMODE = TB_COUNT_UPDOWN;           //upper and down mode
		EPwm2Regs.TBPRD = PWM_CNT_PERIOD; //2500;           // FOR 75KHz with 200MHz TB frequency for UP-DOWN mode

		EPwm2Regs.TBCTL.bit.PHSEN = 1;
		EPwm2Regs.TBPHS.bit.TBPHS = 0;

		EPwm2Regs.CMPCTL.bit.SHDWAMODE = 0;  //shadow compare register
		EPwm2Regs.CMPCTL.bit.LOADAMODE = 0;  //load when CTR = 0;

		EPwm2Regs.CMPA.bit.CMPA = 0;    //duty cycle
		EPwm2Regs.CMPB.bit.CMPB = EPwm2Regs.CMPA.bit.CMPA ;     // duty cycle

		EPwm2Regs.AQCTLA.bit.CAD = AQ_SET;
		EPwm2Regs.AQCTLA.bit.CAU = AQ_CLEAR;
		//EPwm2Regs.AQCTLA.bit.PRD = 1;


		EPwm2Regs.DBCTL.bit.IN_MODE = 0; 	//COMA result is transferred to DB
		EPwm2Regs.DBCTL.bit.POLSEL = DB_ACTV_HIC;//2;
		EPwm2Regs.DBCTL.bit.OUT_MODE = 3;
		EPwm2Regs.DBCTL.bit.OUTSWAP = 0;
		EPwm2Regs.DBRED.bit.DBRED = 50; //0.5us
		EPwm2Regs.DBFED.bit.DBFED = 50;
/*
		///trip zone for RDT
		EPwm2Regs.TZSEL.bit.CBC1 = 1;

		//trip zone for desaturation
		EPwm2Regs.TZSEL.bit.DCAEVT2= 1;
		EPwm2Regs.TZDCSEL.bit.DCAEVT2 = 2;
		EPwm2Regs.DCTRIPSEL.bit.DCAHCOMPSEL = 1;

		//trip zone for overtemperature
		EPwm2Regs.TZSEL.bit.DCBEVT2= 1;
		EPwm2Regs.TZDCSEL.bit.DCBEVT2 = 2;
		EPwm2Regs.DCTRIPSEL.bit.DCBHCOMPSEL = 2;
*/
		EPwm2Regs.TZCTL.bit.TZA = 2;
		EPwm2Regs.TZCTL.bit.TZB = 2;

		// Assumes ePWM clock is already enabled
		EPwm2Regs.ETSEL.bit.SOCBEN	= 1;	        // Disable SOC on A group
		EPwm2Regs.ETSEL.bit.SOCBSEL	= 1;	        // Select SOC on counter = 0
		EPwm2Regs.ETPS.bit.SOCBPRD = 1;		        // Generate pulse on 1st event

	EDIS;
}

void ConfigurePWM6(void )
{
	EALLOW;
	SyncSocRegs.SYNCSELECT.bit.EPWM4SYNCIN = 0;
	ClkCfgRegs.PERCLKDIVSEL.bit.EPWMCLKDIV= 0; //configure the PWM clock the same as system clock
	GpioCtrlRegs.GPAMUX1.bit.GPIO10 = 1;
	GpioCtrlRegs.GPAMUX1.bit.GPIO11 = 1;

	EPwm6Regs.TBCTL.bit.CLKDIV = 0;
	EPwm6Regs.TBCTL.bit.HSPCLKDIV = 0;
	EPwm6Regs.TBCTL.bit.CTRMODE = TB_COUNT_UPDOWN;            //upper and down mode
	EPwm6Regs.TBPRD = PWM_CNT_PERIOD; //2500;           // FOR 75KHz with 200MHz TB frequency for UP-DOWN mode

	EPwm6Regs.TBCTL.bit.PHSEN = 1;
	EPwm6Regs.TBPHS.bit.TBPHS = 0; //2500;

	EPwm6Regs.CMPCTL.bit.SHDWBMODE = 0;  //shadow compare register
	EPwm6Regs.CMPCTL.bit.LOADBMODE = 0;  //load when CTR = 0;

	EPwm6Regs.CMPA.bit.CMPA = 0 ;      //duty cycle
//	EPwm6Regs.CMPB.bit.CMPB = 2000 ;     // duty cycle

	EPwm6Regs.AQCTLA.bit.CAD = 2;
	EPwm6Regs.AQCTLA.bit.CAU = 1;

	EPwm6Regs.DBCTL.bit.IN_MODE = 0; 	//COMA result is transferred to DB
	EPwm6Regs.DBCTL.bit.POLSEL = 2;//2;
	EPwm6Regs.DBCTL.bit.OUT_MODE = 3;
	EPwm6Regs.DBCTL.bit.OUTSWAP = 0;
	EPwm6Regs.DBRED.bit.DBRED = 50; //1.25us
	EPwm6Regs.DBFED.bit.DBFED = 50;
/*
	///trip zone for RDT
	EPwm6Regs.TZSEL.bit.CBC1 = 1;

	//trip zone for desaturation
	EPwm6Regs.TZSEL.bit.DCAEVT2= 1;
	EPwm6Regs.TZDCSEL.bit.DCAEVT2 = 2;
	EPwm6Regs.DCTRIPSEL.bit.DCAHCOMPSEL = 1;

	//trip zone for overtemperature
	EPwm6Regs.TZSEL.bit.DCBEVT2= 1;
	EPwm6Regs.TZDCSEL.bit.DCBEVT2 =
			2;
	EPwm6Regs.DCTRIPSEL.bit.DCBHCOMPSEL = 2;

*/
	EPwm6Regs.TZCTL.bit.TZA = 2;
	EPwm6Regs.TZCTL.bit.TZB = 2;

/*	EPwm6Regs.ETSEL.bit.SOCAEN	= 1;	        // Disable SOC on A group
	EPwm6Regs.ETSEL.bit.SOCASEL	= 1;	        // Select SOC on counter = 0
	EPwm6Regs.ETPS.bit.SOCAPRD = 1;		        // Generate pulse on 1st event
*/
	EDIS;
}

void ConfigurePWM10(void )
{
	EALLOW;

	ClkCfgRegs.PERCLKDIVSEL.bit.EPWMCLKDIV= 0; //configure the PWM clock the same as system clock
	GpioCtrlRegs.GPAGMUX2.bit.GPIO18= 1;
	GpioCtrlRegs.GPAGMUX2.bit.GPIO19= 1;
	GpioCtrlRegs.GPAMUX2.bit.GPIO18 = 1;
	GpioCtrlRegs.GPAMUX2.bit.GPIO19 = 1;

	SyncSocRegs.SYNCSELECT.bit.EPWM10SYNCIN = 0;
	EPwm10Regs.TBCTL.bit.CLKDIV = 0;
	EPwm10Regs.TBCTL.bit.HSPCLKDIV = 0;
	EPwm10Regs.TBCTL.bit.CTRMODE = TB_COUNT_UPDOWN;           //upper and down mode
	EPwm10Regs.TBPRD = PWM_CNT_PERIOD;           // FOR 20KHz with 200MHz TB frequency for UP-DOWN mode
	EPwm10Regs.TBCTL.bit.PHSEN = 1;
	EPwm10Regs.TBPHS.bit.TBPHS = 0; //2500;

	EPwm10Regs.CMPCTL.bit.SHDWAMODE = 0;
	EPwm10Regs.CMPCTL.bit.SHDWBMODE = 0;  //shadow compare register

	EPwm10Regs.CMPA.bit.CMPA = 0 ;      //duty cycle
//	EPwm2Regs.CMPB.bit.CMPB = 2000 ;     // duty cycle

	EPwm10Regs.AQCTLA.bit.CAD = 2;
	EPwm10Regs.AQCTLA.bit.CAU = 1;

	EPwm10Regs.DBCTL.bit.IN_MODE = 0; 	//COMA result is transferred to DB
	EPwm10Regs.DBCTL.bit.POLSEL = 2;//2;
	EPwm10Regs.DBCTL.bit.OUT_MODE = 3;
	EPwm10Regs.DBCTL.bit.OUTSWAP = 0;
	EPwm10Regs.DBRED.bit.DBRED = 50;
	EPwm10Regs.DBFED.bit.DBFED = 50;
	EPwm10Regs.TZCTL.bit.TZA = 2;
	EPwm10Regs.TZCTL.bit.TZB = 2;
/*
	///trip zone for RDT
	EPwm10Regs.TZSEL.bit.CBC1 = 1;

	//trip zone for desaturation
	EPwm10Regs.TZSEL.bit.DCAEVT2= 1;
	EPwm10Regs.TZDCSEL.bit.DCAEVT2 = 2;
	EPwm10Regs.DCTRIPSEL.bit.DCAHCOMPSEL = 1;

	//trip zone for overtemperature
	EPwm10Regs.TZSEL.bit.DCBEVT2= 1;
	EPwm10Regs.TZDCSEL.bit.DCBEVT2 = 2;
	EPwm10Regs.DCTRIPSEL.bit.DCBHCOMPSEL = 2;


	EPwm10Regs.TZCTL.bit.TZA = 2;
	EPwm10Regs.TZCTL.bit.TZB = 2;
*/
	EDIS;
}


void init_adc_conversion ()
{
	Uint16 acqps;

	//determine minimum acquisition window (in SYSCLKS) based on resolution
	if(ADC_RESOLUTION_12BIT == AdcbRegs.ADCCTL2.bit.RESOLUTION){
		acqps = 14; //75ns
	}
	else { //resolution is 16-bit
		acqps = 63; //320ns
	}

	//Select the channels to convert and end of conversion flag
	EALLOW;

	AdcaRegs.ADCSOC0CTL.bit.CHSEL = 0x0;  //SOC0 will convert pin A0
	AdcaRegs.ADCSOC0CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC0CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC0CTL.bit.CHSEL = 0x0;  //SOC0 will convert pin B0
	AdcbRegs.ADCSOC0CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC0CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcaRegs.ADCSOC1CTL.bit.CHSEL = 0x1;  //SOC0 will convert pin A1
	AdcaRegs.ADCSOC1CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC1CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC1CTL.bit.CHSEL = 0x1;  //SOC0 will convert pin B1
	AdcbRegs.ADCSOC1CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC1CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcaRegs.ADCSOC2CTL.bit.CHSEL = 0x2;  //SOC0 will convert pin A2
	AdcaRegs.ADCSOC2CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC2CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC2CTL.bit.CHSEL = 0x2;  //SOC0 will convert pin B2
	AdcbRegs.ADCSOC2CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC2CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcaRegs.ADCSOC3CTL.bit.CHSEL = 0x3;  //SOC0 will convert pin A3
	AdcaRegs.ADCSOC3CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC3CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC3CTL.bit.CHSEL = 0x3;  //SOC0 will convert pin B3
	AdcbRegs.ADCSOC3CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC3CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcaRegs.ADCSOC4CTL.bit.CHSEL = 0x4;  //SOC0 will convert pin A4
	AdcaRegs.ADCSOC4CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC4CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC4CTL.bit.CHSEL = 0x4;  //SOC0 will convert pin B4
	AdcbRegs.ADCSOC4CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC4CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcaRegs.ADCSOC5CTL.bit.CHSEL = 0x5;  //SOC0 will convert pin A5
	AdcaRegs.ADCSOC5CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC5CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC5CTL.bit.CHSEL = 0x5;  //SOC0 will convert pin B5
	AdcbRegs.ADCSOC5CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC5CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

/* those two channels are not connected on the interface board
	AdcaRegs.ADCSOC6CTL.bit.CHSEL = 14;  //SOC0 will convert pin 14
	AdcaRegs.ADCSOC6CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcaRegs.ADCSOC6CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB

	AdcbRegs.ADCSOC6CTL.bit.CHSEL = 15;  //SOC0 will convert pin 15
	AdcbRegs.ADCSOC6CTL.bit.ACQPS = acqps; //sample window is 100 SYSCLK cycles
	AdcbRegs.ADCSOC6CTL.bit.TRIGSEL = 8; //trigger on PWM2 SOCB
*/

	AdcbRegs.ADCINTSEL1N2.bit.INT1SEL = 0x5; //end of SOC5 will set INT1 flag
	AdcbRegs.ADCINTSEL1N2.bit.INT1E = 1;   //enable INT1 flag
	AdcbRegs.ADCINTFLGCLR.bit.ADCINT1 = 1; //make sure INT1 flag is cleared
	EDIS;
}

void InitScibGpio()
{
	 EALLOW;

	       GpioCtrlRegs.GPAPUD.bit.GPIO14 = 0;	   // Enable pull-up for GPIO18 (SCITXDB)
	       GpioCtrlRegs.GPAPUD.bit.GPIO15 = 0;    // Enable pull-up for GPIO15 (SCIRXDB)
	       GpioCtrlRegs.GPAQSEL1.bit.GPIO15 = 3;  // Asynch input GPIO15 (SCIRXDB)
	       GpioCtrlRegs.GPAMUX1.bit.GPIO14 = 2;   // Configure GPIO14 for SCITXDB operation 38pin
	       GpioCtrlRegs.GPAMUX1.bit.GPIO15 = 2;   // Configure GPIO15 for SCIRXDB operation 37pin

	 EDIS;

}

void ConfigureCAN(void)
{
	EALLOW;
    GPIO_SetupPinMux(70, GPIO_MUX_CPU1, 5);  //GPIO30 - CANRXA
    GPIO_SetupPinMux(71, GPIO_MUX_CPU1, 5);  //GPIO31 - CANTXA
    GPIO_SetupPinOptions(70, GPIO_INPUT, GPIO_ASYNC);
    GPIO_SetupPinOptions(71, GPIO_OUTPUT, GPIO_PUSHPULL);

    CANInit(CANA_BASE);
    CANClkSourceSelect(CANA_BASE, 0);

    CANBitRateSet(CANA_BASE, 200000000, 500000);

   // HWREG(CANA_BASE + CAN_O_CTL) |= 0x0;//CAN_CTL_TEST;
  //  HWREG(CANA_BASE + CAN_O_TEST) = 0x0;// CAN_TEST_EXL;
    HWREG(CANA_BASE + CAN_O_CTL) |= 0x200;//auto bus on

    CANEnable(CANA_BASE);
    EDIS;
}

float PI_Controller_PLL( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

	static float e1 = 0;
	static float y1 = 0;

	if (reset == 1)
	{
		e1 = 0;
		y1 = 0;
		return 0;
	}
	else
	{
		float y = (Ki*T/2)*(e+e1) + y1;

		if ( y > windup_limit ) y = windup_limit;
		if ( y < -windup_limit ) y = -windup_limit;
		e1 = e;
		y1 = y;

		return y + Kp*e;
	}
}


float PI_Controller_Qower( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

	static float e1 = 0;
	static float y1 = 0;

	if (reset == 1)
	{
		e1 = 0;
		y1 = 0;
		return 0;
	}
	else
	{
		float y = (Ki*T/2)*(e+e1) + y1;

		if ( y > windup_limit ) y = windup_limit;
		if ( y < -windup_limit ) y = -windup_limit;
		e1 = e;
		y1 = y;

		return y + Kp*e;
	}
}


float PI_Controller_Power( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

    static float e1 = 0;
    static float y1 = 0;

    if (reset == 1)
    {
        e1 = 0;
        y1 = 0;
        return 0;
    }
    else
    {
        float y = (Ki*T/2)*(e+e1) + y1;

        if ( y > windup_limit ) y = windup_limit;
        if ( y < -windup_limit ) y = -windup_limit;
        e1 = e;
        y1 = y;

        return y + Kp*e;
    }
}



float PI_Controller_V1( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

	static float e1 = 0;
	static float y1 = 0;

	if (reset ==1)
	{
		e1 = 0;
		y1 = 0;
		return 0;
	}
	else
	{
		float y = (Ki*T/2)*(e+e1) + y1;

		if ( y > windup_limit ) y = windup_limit;
		if ( y < -windup_limit ) y = -windup_limit;
		e1 = e;
		y1 = y;

		return y + Kp*e;
	}
}

float PI_Controller_V2( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

	static float e1 = 0;
	static float y1 = 0;

	if (reset ==1)
	{
		e1 = 0;
		y1 = 0;
		return 0;
	}
	else
	{
		float y = (Ki*T/2)*(e+e1) + y1;

		if ( y > windup_limit ) y = windup_limit;
		if ( y < -windup_limit ) y = -windup_limit;
		e1 = e;
		y1 = y;

		return y + Kp*e;
	}
}

float PI_Controller_I1( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

	static float e1 = 0;
	static float y1 = 0;

	if (reset ==1)
	{
		e1 = 0;
		y1 = 0;
		return 0;
	}
	else
	{
		float y = (Ki*T/2)*(e+e1) + y1;

		if ( y > windup_limit ) y = windup_limit;
		if ( y < -windup_limit ) y = -windup_limit;
		e1 = e;
		y1 = y;

		return y + Kp*e;
	}
}

float PI_Controller_I2( float e, float Kp, float Ki, float T, float windup_limit, int reset)
{

	static float e1 = 0;
	static float y1 = 0;

	if (reset ==1)
	{
		e1 = 0;
		y1 = 0;
		return 0;
	}
	else
	{
		float y = (Ki*T/2)*(e+e1) + y1;

		if ( y > windup_limit ) y = windup_limit;
		if ( y < -windup_limit ) y = -windup_limit;
		e1 = e;
		y1 = y;

		return y + Kp*e;
	}
}

float M_clamp_ac( float M )
{
	if ( M > 0.99 ) M = 0.99;
	if ( M < -0.99 ) M = -0.99;
	return M;
}

float M_clamp_dc( float M )
{
	if ( M > 0.99 ) M = 0.99;
	if ( M < 0.01 ) M = 0.01;
	return M;
}

int DC_voltage_is_OK(float DC_voltage)
{
	if ( 370 <= DC_voltage && DC_voltage <= 450)
		return 1;
	else
		return 0;
}

int battery_voltage_is_OK(float Battery_voltage)
{
	if ( 120 <= Battery_voltage && Battery_voltage <= 165)
		return 1;
	else
		return 0;
}

void trip_all_switches()
{
	EALLOW;

		EPwm2Regs.TZFRC.bit.OST = 1;
		EPwm6Regs.TZFRC.bit.OST = 1;
		EPwm10Regs.TZFRC.bit.OST = 1;

	EDIS;
}

void untrip_all_switches()
{
	EALLOW;

		EPwm2Regs.TZCLR.bit.OST = 1;
		EPwm2Regs.TZCLR.bit.INT = 1;

		EPwm6Regs.TZCLR.bit.OST = 1;
	    EPwm6Regs.TZCLR.bit.INT = 1;

		EPwm10Regs.TZCLR.bit.OST = 1;
		EPwm10Regs.TZCLR.bit.INT = 1;



	EDIS;
}

int software_trip_is_active()
{
	if (EPwm2Regs.TZFLG.bit.OST == 1 && EPwm6Regs.TZFLG.bit.OST == 1)
		return 1;
	else
		return 0;
}

void reset_all_relays()
{
	GpioDataRegs.GPBCLEAR.bit.GPIO61 = 1; //RELAY-1
	GpioDataRegs.GPBCLEAR.bit.GPIO41 = 1; //RELAY-2
	GpioDataRegs.GPCCLEAR.bit.GPIO65 = 1; //RELAY-3
	GpioDataRegs.GPCCLEAR.bit.GPIO69 = 1; //RELAY-4

	GpioDataRegs.GPBSET.bit.GPIO61 = 0; //RELAY-1
	GpioDataRegs.GPBSET.bit.GPIO41 = 0; //RELAY-2
	GpioDataRegs.GPCSET.bit.GPIO65 = 0; //RELAY-3
	GpioDataRegs.GPCSET.bit.GPIO69 = 0; //RELAY-4

}

void reset_relay_1and3 ()
{
	GpioDataRegs.GPBCLEAR.bit.GPIO61 = 1; //RELAY-1
	GpioDataRegs.GPCCLEAR.bit.GPIO65 = 1; //RELAY-3

	GpioDataRegs.GPBSET.bit.GPIO61 = 0; //RELAY-1
	GpioDataRegs.GPCSET.bit.GPIO65 = 0; //RELAY-3

}

void reset_relay_2and4 ()
{
	GpioDataRegs.GPBCLEAR.bit.GPIO41 = 1; //RELAY-2
	GpioDataRegs.GPCCLEAR.bit.GPIO69 = 1; //RELAY-4

	GpioDataRegs.GPBSET.bit.GPIO41 = 0; //RELAY-2
	GpioDataRegs.GPCSET.bit.GPIO69 = 0; //RELAY-4

}

void set_relay_1and3 ()
{
	GpioDataRegs.GPBSET.bit.GPIO61 = 1; //RELAY-1
	GpioDataRegs.GPCSET.bit.GPIO65 = 1; //RELAY-3

	GpioDataRegs.GPBCLEAR.bit.GPIO61 = 0; //RELAY-1
	GpioDataRegs.GPCCLEAR.bit.GPIO65 = 0; //RELAY-3
}

void set_relay_2and4 ()
{
	GpioDataRegs.GPBSET.bit.GPIO41 = 1; //RELAY-2
	GpioDataRegs.GPCSET.bit.GPIO69 = 1; //RELAY-4

	GpioDataRegs.GPBCLEAR.bit.GPIO41 = 0; //RELAY-2
	GpioDataRegs.GPCCLEAR.bit.GPIO69 = 0; //RELAY-4

}

int relay_1and3_is_set()
{
	if(GpioDataRegs.GPBDAT.bit.GPIO61 == 1 && GpioDataRegs.GPCDAT.bit.GPIO65 ==1)
		return 1;
	else
		return 0;
}

int relay_2and4_is_set()
{
	if(GpioDataRegs.GPBDAT.bit.GPIO41 == 1 && GpioDataRegs.GPCDAT.bit.GPIO69 ==1)
		return 1;
	else
		return 0;
}

int grid_voltage_is_locked(float Vac_mag, float w)
{
	static int grid_voltage_is_ok_cnt = 0;
	static int grid_voltage_is_bad_cnt = 0;
	static int last_state = 0;

	if ( 350 <= Vac_mag && Vac_mag <= 450 && 370.7079 <= w && w <= 383.2743 )
	{
		grid_voltage_is_bad_cnt = 0 ;
		if ( grid_voltage_is_ok_cnt < 300)
			grid_voltage_is_ok_cnt = grid_voltage_is_ok_cnt + 1;
	}
	else
	{
		grid_voltage_is_ok_cnt = 0;
		if ( grid_voltage_is_bad_cnt < 10)
			grid_voltage_is_bad_cnt = grid_voltage_is_bad_cnt + 1;
	}

	if( grid_voltage_is_ok_cnt >= 300)
	{
		last_state = 1;
		return 1;
	}
	else if (grid_voltage_is_bad_cnt >= 10)
	{
		last_state = 0;
		return 0;
	}
	else
		return last_state;
}

int cap_voltage_is_grid_voltage(float cap_votlage_d, float cap_votlage_q, float grid_voltage_d, float grid_voltage_q)
{
	static int cap_voltage_is_grid_voltage_cnt = 0;

	if ( (grid_voltage_d - cap_votlage_d) <10 && (grid_voltage_d - cap_votlage_d) > -10 &&  (grid_voltage_q- cap_votlage_q) < 10 && (grid_voltage_q - cap_votlage_q) > -10 )
	{

		if ( cap_voltage_is_grid_voltage_cnt < 1000)
			cap_voltage_is_grid_voltage_cnt = cap_voltage_is_grid_voltage_cnt + 1;
	}
	else
	{
		cap_voltage_is_grid_voltage_cnt = 0;
	}

	if( cap_voltage_is_grid_voltage_cnt >= 300)
	{
		return 1;
	}
	else
		return 0;
}
