
/* $Id: engine.c 61 2008-02-22 23:18:59Z jessekornblum $ */

#include "main.h"

#define MAX_STATUS_MSG   78

int hash_file(state *s, TCHAR *fn)
{
  size_t fn_length;
  char *sum;
  TCHAR *my_filename, *msg;
  FILE *handle;
  
  handle = _tfopen(fn,_TEXT("rb"));
  if (NULL == handle)
  {
    print_error_unicode(s,fn,"%s", strerror(errno));
    return TRUE;
  }
 
  if ((sum = (char *)malloc(sizeof(char) * FUZZY_MAX_RESULT)) == NULL)
  {
    fclose(handle);
    print_error_unicode(s,fn,"%s", strerror(errno));
    return TRUE;
  }

  if ((msg = (TCHAR *)malloc(sizeof(TCHAR) * (MAX_STATUS_MSG + 2))) == NULL)
  {
    free(sum);
    fclose(handle);
    print_error_unicode(s,fn,"%s", strerror(errno));
    return TRUE;
  }

  if (MODE(mode_verbose))
  {
    fn_length = _tcslen(fn);
    if (fn_length > MAX_STATUS_MSG)
    {
      // We have to make a duplicate of the string to call basename on it
      // We need the original name for the output later on
      my_filename = _tcsdup(fn);
      my_basename(my_filename);
    }
    else
      my_filename = fn;

    _sntprintf(msg,
	       MAX_STATUS_MSG-1,
	       _TEXT("Hashing: %s%s"), 
	       my_filename, 
	       _TEXT(BLANK_LINE));
    _ftprintf(stderr,_TEXT("%s\r"), msg);

    if (fn_length > MAX_STATUS_MSG)
      free(my_filename);
  }

  fuzzy_hash_file(handle,sum);
  prepare_filename(s,fn);

  if (MODE(mode_match_pretty))
  {
    if (match_add(s,fn,sum))
      print_error_unicode(s,fn,"Unable to add hash to set of known hashes");
  }
  else if (MODE(mode_match) || MODE(mode_directory))
  {
    match_compare(s,fn,sum);

    if (MODE(mode_directory))
      if (match_add(s,fn,sum))
	print_error_unicode(s,fn,"Unable to add hash to set of known hashes");
  }
  else
  {
    if (s->first_file_processed)
    {
      printf ("%s%s", OUTPUT_FILE_HEADER,NEWLINE);
      s->first_file_processed = FALSE;
    }
    printf ("%s,\"", sum);
    display_filename(stdout,fn);
    print_status("\"");
  }

  fclose(handle);
  free(sum);
  free(msg);
  return FALSE;
}

