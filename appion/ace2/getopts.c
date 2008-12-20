/* getopts.c - Command line argument parser
 *
 * Whom: Steve Mertz <steve@dragon-ware.com>
 * Date: 20010111
 * Why:  Because I couldn't find one that I liked. So I wrote this one.
 *
*/
/*
 * Copyright (c) 2001-2004 Steve Mertz <steve@dragon-ware.com>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without 
 * modification, are permitted provided that the following conditions are met:
 *
 * Redistributions of source code must retain the above copyright notice, this 
 * list of conditions and the following disclaimer.
 * 
 * Redistributions in binary form must reproduce the above copyright notice, 
 * this list of conditions and the following disclaimer in the documentation 
 * and/or other materials provided with the distribution.
 * 
 * Neither the name of Dragon Ware nor the names of its contributors may be 
 * used to endorse or promote products derived from this software without 
 * specific prior written permission. 
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR 
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS 
 * OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
 *
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "getopts.h"

int option_index = 1;

/* int getopts_usage()
 *
 *  Returns: 1 - Successful
 */

char * getopt_usage( struct options opt ) {
	
	size_t cmd_length = 15;
	
	if ( opt.name ) cmd_length += strlen(opt.name);
	if ( opt.shortName ) cmd_length += strlen(opt.shortName);
	if ( opt.description ) cmd_length += strlen(opt.description);
	
	char * cmd = calloc(1,sizeof(char)*cmd_length);
	if ( cmd == NULL ) return NULL;
	
	if (opt.name && opt.shortName ) {
			
		if ( opt.args ) sprintf(cmd, "--%s,\t-%s <args>\t\t", opt.name, opt.shortName);
		else sprintf(cmd, "--%s,\t-%s\t\t\t", opt.name, opt.shortName);

	} else if ( opt.name ) {

		if (opt.args) sprintf(cmd, "--%s <args>\t\t\t", opt.name);
		else sprintf(cmd, "--%s\t\t\t", opt.name);
			
	} else if (opt.shortName) {

		if (opt.args) sprintf(cmd, "\t\t-%s <args>\t\t", opt.shortName);
		else sprintf(cmd, "\t\t-%s\t\t\t", opt.shortName);
			
	}
		
	if ( opt.description ) strcat(cmd,opt.description);
	
	return cmd;
	
}

int getopts_usage(char *progName, struct options opts[]) {
	
	int count;
	char * cmd = NULL;
  
	fprintf(stderr,"Usage: %s [options]\n\n", progName);
	fprintf(stderr,"  --help,\t-h\t\t\tDisplays this information\n");
 
	for (count = 0; opts[count].description; count++) {
		cmd = getopt_usage(opts[count]);
		fprintf(stderr,"  %s\n", cmd);
		free(cmd);
		
	}
	
	return 1;
	
}

/* int getopts()
 *
 * Returns: -1 - Couldn't allocate memory.  Please handle me. 
 *          0  - No arguments to parse
 *          #  - The number in the struct for the matched arg.
 *
*/

int getopts(int argc, char **argv, struct options opts[], char arg[] ) {

	int argCounter, sizeOfArgs;
	if (  argc <= 1 || option_index == argc ) return 0;
  
	for (argCounter = 1; argCounter < argc; argCounter++) {
		if ( !strcmp(argv[argCounter], "-h") || !strcmp(argv[argCounter], "--help")) {
			useage:
			getopts_usage(argv[0], opts);
			exit(0);
		}
	}

	if ( option_index > argc ) return 0;
	
	for ( argCounter = 0; opts[argCounter].number != 0 ; argCounter++ ) {
		if ( (opts[argCounter].name && !strcmp(opts[argCounter].name,argv[option_index]+2)) || (opts[argCounter].shortName && !strcmp(opts[argCounter].shortName,argv[option_index]+1)) ) {
			if ( opts[argCounter].args ) {
				option_index++;
				if (option_index >= argc) {
					char * cmd = getopt_usage(opts[argCounter]);
					fprintf(stderr,"!!!! Improper use of option %s !!!!\n%s\n",opts[argCounter].shortName,cmd);
					option_index++;
					free(cmd);
					return 0;
				}		
/* This grossness that follows is to support having a '-' in the argument. */

				if (*argv[option_index] == '-') {
					int optionSeeker;
					for (optionSeeker = 0; opts[optionSeeker].description; optionSeeker++) {
						if ((opts[optionSeeker].name && !strcmp(opts[optionSeeker].name, (argv[option_index]+2))) || (opts[optionSeeker].shortName && !strcmp(opts[optionSeeker].shortName, (argv[option_index]+1)))) {
							char * cmd = getopt_usage(opts[argCounter]);
							fprintf(stderr,"!!!! Improper use of option %s !!!!\n%s\n",opts[argCounter].shortName,cmd);
							option_index++;
							free(cmd);
							return 0;
						}
					}
				}
		
/* End of gross hack for supporting '-' in arguments. */
						
				sprintf(arg,"%s",argv[option_index]);
					
			}
				
			option_index++;

			return opts[argCounter].number;
				
		}
	}
			
/** The Option doesn't exist.  We should warn them. */
	if (*argv[option_index] == '-') {
		fprintf(stderr,"!!!! Argument %s is not understood !!!!",argv[option_index]);
		option_index++;
		return 0;
	}
		
}







