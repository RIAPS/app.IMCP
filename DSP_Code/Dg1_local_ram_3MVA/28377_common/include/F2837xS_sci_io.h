//###########################################################################
//
// FILE:   F2837xS_sci_io.h
//
// TITLE:  Prototypes for SCI redirection to STDIO
//
//###########################################################################
// $TI Release: F2837xS Support Library v200 $
// $Release Date: Tue Jun 21 13:52:16 CDT 2016 $
// $Copyright: Copyright (C) 2014-2016 Texas Instruments Incorporated -
//             http://www.ti.com/ ALL RIGHTS RESERVED $
//###########################################################################

#ifndef F2837xS_SCI_IO_H
#define F2837xS_SCI_IO_H

#ifdef __cplusplus
extern "C" {
#endif

//
// Function Prototypes
//
extern int SCI_open(const char * path, unsigned flags, int llv_fd);
extern int SCI_close(int dev_fd);
extern int SCI_read(int dev_fd, char * buf, unsigned count);
extern int SCI_write(int dev_fd, char * buf, unsigned count);
extern off_t SCI_lseek(int dev_fd, off_t offset, int origin);
extern int SCI_unlink(const char * path);
extern int SCI_rename(const char * old_name, const char * new_name);

#ifdef __cplusplus
}
#endif /* extern "C" */


#endif

//
// End of file
//
