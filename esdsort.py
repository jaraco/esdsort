/*                                ESDSORT.C                               *
 *   This program takes a result file from an ElectroStatic Discharge     *
 * evaluation and compiles the information into four different files that *
 * are more useful and understandable.  Detailed documentation is located *
 * in a file called ESDSORT.DOC.                                          *
 *                   copyright Signetics  1992                            *
 *                    written by Jason Coombs                             */

#include <stdio.h>
#include <string.h>
#define FAIL 0
#define PASS 1
#define MAXLINE 100
#define MAXPARTS 3000
#define MAXVOLTAGES 10
#define FF 12    /* Character for form feed */
#define MAXNAME 17   /* Maximum length for process and design names */

char buf[MAXNAME];

main(argc, argv)
int argc;
char *argv[];
{
  struct type  {
    int icc, ipd, inph, inpl, iodh, iodl,
      iozh, iozl, odh, odl, ozh, ozl, cont;
  };
  struct _part  {
    int sn;
    int voltage;
    char pass;
    char sr;
    struct type failtype;
    int resval;
    char design, process, processname[MAXNAME], designname[MAXNAME];
  } part[MAXPARTS];

  char inline[MAXLINE], tempstring[MAXLINE], propage, despage;
  int position, part_count = 0, count, failcode,
    i, e, save, paglen, newdes, voltages[MAXVOLTAGES], total[30],
    fails[30];

  FILE *temp, *infile, *statfile, *resultfile, *fopen();

  printf("\n\n                 ESD data file sorting utility\n");
  printf("                    written by Jason Coombs\n");
  printf("                   Copyright Signetics  1992\n\n\n");

  if ((temp = fopen("esdsort.dat", "w")) != NULL) fclose(temp);
  if (argc == 1)
    fprintf(stderr,
    "Please re-enter command line with the name of the file to be sorted.\n");
  else
    while (--argc > 0)
      if((infile = fopen(*++argv, "r")) == NULL)  {
        fprintf(stderr, "Can't open %s.\nPlease check path and filename.\n", *argv);
        exit(1);
      }
      else  {
        printf("Processing file %s\n", *argv);
        if((statfile = fopen("esdsort.dat", "a")) == NULL)  {
          fprintf(stderr, "Cannot open output file %s.", "esdsort.dat");
          exit(1);
        }
        else while (fgets(inline,MAXLINE,infile) != NULL)  {
          if((position = (textfind(&inline, "@"))) != EOF)  {
            position++;
            for(count = 0 ; inline[position+count] != ` ` ; count++)
              tempstring[count] = inline[position + count];
            tempstring[count] = `\0`;
            part[part_count].voltage = atoi(tempstring);
            if(toupper(tempstring[1]) == 'K')
              part[part_count].voltage = (part[part_count].voltage * 1000);
          }

          if((position = (textfind(&inline, "S/N"))) != EOF)  {
            position = position + 6;
            ++part_count;
            part[part_count].sr = 'N';
            part[part_count].failtype.icc    =
              part[part_count].failtype.ipd  =
              part[part_count].failtype.inph =
              part[part_count].failtype.inpl =
              part[part_count].failtype.iodh =
              part[part_count].failtype.iodl =
              part[part_count].failtype.iozh =
              part[part_count].failtype.iozl =
              part[part_count].failtype.odh  =
              part[part_count].failtype.odl  =
              part[part_count].failtype.ozh  =
              part[part_count].failtype.ozl  =
              part[part_count].failtype.cont = 0;
            part[part_count].pass = 'Y';

            if(inline[position] == ' ')  {
              if(inline[position+1] == ' ')
                position = position + 2;
              else
                position = position + 1;
            }
            for(count=0; count < 4; count++)
              tempstring[count] = inline[position + count];
            tempstring[count] = '\0';
            part[part_count].sn = atoi(tempstring);
            if(ser2pro(part[part_count].sn) != NULL)  {
              strcpy(part[part_count].processname,
                ser2pro(part[part_count].sn));
              part[part_count].process = part[part_count].processname[0];
            }
            else  {
              strcpy(part[part_count].processname,"P Process");
              part[part_count].process = 'P';
            }
          }

          if(textfind(&inline, "   ****") != EOF)  {
            part[part_count].pass = 'N';
            for(count=0; count<3; count++)
              tempstring[count] = inline[count + 3];
            tempstring[count] = '\0';
            failcode = atoi(tempstring);
            switch(failcode)  {
              case 860:
              case 881:
                part[part_count].failtype.icc++;
                break;
              case 790:
              case 813:
                part[part_count].failtype.ipd++;
                break;
              case 524:
                part[part_count].failtype.inph++;
                break;
              case 544:
                part[part_count].failtype.inpl++;
                break;
              case 615:
                part[part_count].failtype.iodh++;
                break;
              case 634:
                part[part_count].failtype.iodl++;
                break;
              case 574:
                part[part_count].failtype.iozh++;
                break;
              case 593:
                part[part_count].failtype.iozl++;
                break;
              case 697:
                part[part_count].failtype.odh++;
                break;
              case 716:
                part[part_count].failtype.odl++;
                break;
              case 656:
                part[part_count].failtype.ozh++;
                break;
              case 675:
                part[part_count].failtype.ozl++;
                break;
              case 315:
                part[part_count].failtype.cont++;
                break;
              case 938:
                pprintf("Identity fail.  Check status file esdsort.dat\n");
                fprintf(statfile,"Identity fail on sn%d\n",part[part_count].sn);
                fprintf(statfile,"Zapped at %d volts\n\n",part[part_count].voltage);
                break;
              default:
                printf("Error!!!  Undefined fail code %d.\n", failcode);
                break;
            }
          }
          if(textfind(&inline, "938") == 4)  {
            for(count=0;count<3;count++)
              tempstring[count] = inline[14 + count];
            tempstring[count] = '\0';
            part[part_count].resval = atoi(tempstring);
            if(res2des(part[part_count].resval) != NULL)  {
              strcpy(part[part_count].designname,
                res2des(part[part_count].resval));
              part[part_count].design = part[part_count].designname[0];
            }
            else  {
              strcpy(part[part_count].designname,"D Design");
              part[part_count].design = 'D';
            }
          }
          if(textfind(&inline, "FAIL") == 20)  {
            part[part_count].pass = 'N';
            part[part_count].sr = 'Y';
          }
          else
            part[part_count].sr = 'N';
        }
      printf("Sorting successful!\n\n");
      fclose(infile);
      fclose(statfile);
  }
  if(part_count > 0)  {
    printf("Total parts: %d\n", part_count);

          /*              Make Result Files                     */

    if((resultfile = fopen("results.fails", "w")) = NULL)  {
      fprintf(stderr, "\nCannot open output file as %s.", "results.fails");
      exit(1);
    }
    else  {
      char header[100] =
        "SN     P  SR  ICC  IPD  INPH INPL IODH IODL IOZH IOZL ODH ODL OZH OZL CONT";
      printf("\nCreating result files.\n");
      pageln = save = 0;

      for(position = 1; position <= part_count; position++)  {
        if(part[position].voltage != part[save].voltage)  {
          save = position;
          propage = 'A';
        }
        while(propage < 'M')  {
          despage = 'A';

          for(i=0,i<part_count;++i)  {
            if(part[i].voltage == part[save].voltage &&
              part[i].process == propage)  {
              while(despage < 'M')  {
                newdes = 'Y';
                for(e=0;e<part_count;++e) {

                  if(paglen > 60 || pagelen == 0)  {
                    fprintf(resultfile,"%c\n%dV\n%s\n",
                      FF,part[save].voltage,header);
                    for(count = 0; count < 76; ++count)
                      {fprintf(resultfile, "=");}
                    fprintf(resultfile, "\n%s\n", part[i].processname);
                    paglen = 6;
                  }
                  if(part[e].voltage == part[save].voltage &&
                    part[e].process == propage &&
                    part[e].design == despage)  {
                    if(newdes == 'Y')  {
                      fprintf(resultfile, "\n");
                      paglen++;
                      newdes = 'N';
                    }
                    pagelen++;
            fprintf(resultfile,
              "%c %4d %c  %c",part[e].design,part[e].sn,
              part[e].pass,part[e].sr);
            if(part[e].failtype.icc > 0) fprintf(resultfile,
              "   %d",part[e].failtype.icc);


            else fprintf(resultfile,"    ");
            if(part[e].failtype.ipd > 0) fprintf(resultfile,
              "    %d",part[e].failtype.ipd);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.inph > 0) fprintf(resultfile,
              "    %d",part[e].failtype.inph);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.inpl > 0) fprintf(resultfile,
              "    %d",part[e].failtype.inpl);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.iodh > 0) fprintf(resultfile,
              "    %d",part[e].failtype.iodh);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.iodl > 0) fprintf(resultfile,
              "    %d",part[e].failtype.iodl);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.iozh > 0) fprintf(resultfile,
              "    %d",part[e].failtype.iozh);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.iozl > 0) fprintf(resultfile,
              "    %d",part[e].failtype.iozl);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.odh > 0) fprintf(resultfile,
              "    %d",part[e].failtype.odh);
            else fprintf(resultfile,"     ");
            if(part[e].failtype.odl > 0) fprintf(resultfile,
              "   %d",part[e].failtype.odl);
            else fprintf(resultfile,"    ");
            if(part[e].failtype.ozh > 0) fprintf(resultfile,
              "   %d",part[e].failtype.ozh);
            else fprintf(resultfile,"    ");
            if(part[e].failtype.ozl > 0) fprintf(resultfile,
              "   %d",part[e].failtype.ozl);
            else fprintf(resultfile,"    ");
            if(part[e].failtype.cont > 0) fprintf(resultfile,
              "    %d\n",part[e].failtype.cont);
            else fprintf(resultfile,"    \n");
                  }
                }
                despage++;
              }
            }
          }
          paglen = 0;
          propage++;
        }
      }
      fclose(resultfile);
    }

    for(position = 1; position <= part_count; position++)  {
      for(count = 0;count<MAXVOLTAGES; count++)  {
        if(part[position]voltage  == voltages[count]) break;
        if(voltages[count] == 0)  {
          voltages[count] = part[position].voltage;
          break;
    } } }

    if((resultfile = fopen("results.proc", "w")) == NULL)  {
      fprintf(stderr, "\nCannot open output file %s.", "results.proc");
      exit(1);
    }
    else  {

      for(propage = 'A';propage<'M';propage++)  {
        paglen = 0;
        for(despage = 'A'; despage<'M'; despage++)  {
          for(count = 1;count<=part_count;count++)  {
            for(position = 0; voltages[position] != 0;position++)  {
              total[position] = fails[position] = 0;
              if(part[count].process == propage
                && part[count].design == despage)  {
                if(paglen == 0 || paglen > 60)  {
                  paglen = 6;
                  fprintf(resultfile,"%c\nPROCESS %s\n           DESIGN    ",
                    FF,part[count].processname);
                  for(i = 0; voltages[i] != 0; i++)  {
                    fprintf(resultfile,"%3.1fKV  ",(float)voltages[i]/1000);
                  }
                  fprintf(resultfile,"\n");
                  for(i = 0;i < 76; ++i)  {fprintf(resultfile,"=");}
                  fprintf(resultfile,"\n\n");
                }
                for(e = 1;e <= part_count;e++)  {

                  if(part[e].process == propage
                    && part[e].design == despage
                    && part[e].voltage == voltages[position])  {
                    total[position]++;
                    if(part[e].pass == 'N') fails[position]++;
                  }
                }
              }
            }
            if(part[count].design == despage
              && part[count].process == propage)  {

              fprintf(resultfile,"%17s    ",part[count].designname);
              for(position = 0;voltages[position] != 0; position++)  {
                if(total[position] != 0)
                  fprintf(resultfile,"%2d/%2d  ",
                    fails[position],total[position]);
                else
                  fprintf(resultfile,"       ");
              }
              fprintf(resultfile,"\n");
              for(i = 0;i < 76; ++i)  {fprintf(resultfile,"_");}
              fprintf(resultfile,"\n\n");
              paglen = paglen + 3;
              break;
            }
          }
        }
      }
      fclose(resultfile);
    }

    if((resultfile = fopen("results.volt", "w")) == NULL)  {
      fprintf(stderr, "\nCannot open output file %s.", "results.volt");
      exit(1);
    }
    else  {
      for(position = 0; voltages[position] != 0; position++)  {
        paglen = 0;
        for(despage = 'A'; despage<'M'; despage++)  {
          for(count = 1;count<=part_count;count++)  {
            for(propage = 'A';propage<'M';propage++)  {
              total[propage - 'A'] = fails[propage - 'A'] = 0;
              if(part[count].voltage == voltages[position]
                && part[count].design == despage)  {
                if(paglen == 0 || paglen > 60)  {
                  paglen = 6;


                  fprintf(resultftile,
                    "%c\nVOLTAGE %4d\t\t\tPROCESS\n           DESIGN   ",
                    FF,voltages[position]);
                  for(i = 'A'; i < 'M'; i = i + 2)  {
                    if(i = 'L')  fprintf(resultfile,"%c",i);
                    else fprintf(resultfile,"%c       ",i);
                  }
                  fprintf(rresultfile,"\n                 ");
                  for(i = 'B'; i < 'N'; i = i + 2)  {
                    fprintf(resultfile,"       %c",i);
                  }
                  fprintf(resultfile,"\n");
                  for(i = 0;i < 76; ++i)  {fprintf(resultfile,"=");}
                  fprintf(resultfile,"\n\n");
                }
                for(e = 1;e <= part_count;e++)  {

                  if(part[e].process == propage
                    && part[e].design == despage
                    && part[e].voltage == voltages[position])  {
                    total[propage-'A']++;
                    if(part[e].pass == 'N') fails[propage-'A']++;
                  }
                }
              }
            }
            if(part[count].design == despage
              && part[count].voltage == voltages[position])  {

              fprintf(resultfile,"%17s   ",part[count].designname);
              for(propage = 'A'; propage < 'M'; propage = propage + 2)  {
                if(total[propage-'A'] != 0)
                  fprintf(resultfile,"%2d/%2d   ",
                    fails[propage-'A'],total[propage - 'A']);
                else
                  fprintf(resultfile,"        ");
              }

              fprintf(resultfile,"\n                        ");
              for(propage = 'B'; propage < 'N'; propage = propage + 2)  {
                if(total[propage-'A'] != 0)
                  fprintf(resultfile,"%2d/%2d   ",
                    fails[propage-'A'],total[propage - 'A']);
                else
                  fprintf(resultfile,"        ");
              }
              fprintf(resultfile,"\n");
              for(i = 0;i < 76; ++i)  {fprintf(resultfile,"_");}
              fprintf(resultfile,"\n\n");
              paglen = paglen + 3;
              break;
            }
          }
        }
      }
      fclose(resultfile);
    }

  }
}

filecopy(infile)
FILE *infile;
{


  int c;

  while ((c=getc(infile)) != EOF)
    putc(c, stdout);
}

int textfind(line, text)  /* Search for 'text' in 'line' */
char *line;
char text[9];
{
  int i=0, n=0, status;

  while(*(line+i) != '\n')  {
    if (*(line+i) == text[n])  {
      for(n=0; n<strlen(text); n++)  {
        if (*(line+i+n) != text[n])  {
          status = FAIL;
          break;
        }
        else status = PASS;
      }
      if(status == PASS) return(i+1);
      else  {
        i++;
        n=0;
      }
    }
    else i++;
  }
  return(EOF);
}

atoi(s)    /* Convert s to integer value */char s[];
{
  int i, n;

  n = 0;
  for (i = 0; s[i] >= '0' && s[i] <= '9'; ++i)
    n = 10*n + s[i] - '0';
  return(n);
}

ser2pro(sn)
int sn;
{
  FILE *init, *fopen();
  int counter= 0,i,low, high;
  char inline[MAXLINE];

  if((init = fopen("PROCESS.DAT", "r")) != NULL)  {
    while (fgets(inline,MAXLINE,init) != NULL)  {
      if(inline[0] < '0' || inline[0] > '9') continue;
      counter = atoi(inline);
      for(i=0;i<counter;i++)  {
        low = atoi(inline + 2 + (10*i));
        high = atoi(inline + 7 + (10*i));
        if(sn >= low && sn <= high)
          strcpy(buf,(inline + 2 + (10*counter)));
      }
    }
    for(i = 0;i < MAXNAME;i++)  {
      if(buf[i] == '\n')  {
        buf[i] = '\0';

        break;
      }
    }
    fclose(init);
    return(buf);
  }
  fclose(init);
  return(NULL);
}

res2des(resval)
int resval;
{
  FILE *init, *fopen();
  int counter= 0,i,low, high;
  char inline[MAXLINE];

  if((init = fopen("DESIGN.DAT", "r")) != NULL)  {
    while (fgets(inline,MAXLINE,init) != NULL)  {
      if(inline[0] < '0' || inline[0] > '9') continue;
      counter = atoi(inline);
      for(i=0;i<counter;i++)  {
        low = atoi(inline + 2 + (10*i));
        high = atoi(inline + 7 + (10*i));
        if(resval >= low && resval <= high)
          strcpy(buf,(inline + 2 + (10*counter)));
      }
    }
    for(i = 0; i < MAXNAME;i++)  {
      if(buf[i] == '\n')  {
        buf[i] = '\0';
        break;
      }
    }
    fclose(init);
    return(buf);
  }
  fclose(init);
  return(NULL);
}
