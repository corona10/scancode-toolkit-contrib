#
# Copyright (c) 2017 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/scancode-toolkit/
# The ScanCode software is licensed under the Apache License version 2.0.
# Data generated with ScanCode require an acknowledgment.
# ScanCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with ScanCode or any ScanCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with ScanCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  ScanCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  ScanCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/scancode-toolkit/ for support and download.

from __future__ import absolute_import, print_function

import logging

import pefile

from commoncode import text
from typecode import contenttype
from contextlib import closing
from collections import OrderedDict


logger = logging.getLogger(__name__)

"""
Extract data from windows PE DLLs and executable.

Note that the extraction may not be correct for all PE in particular older
legacy PEs.

See tests and:
    http://msdn.microsoft.com/en-us/library/aa381058%28v=VS.85%29.aspx

PE stores data in a "VarInfo" structure for "variable information".
VarInfo are by definition variable key/value pairs:
    http://msdn.microsoft.com/en-us/library/ms646995%28v=vs.85%29.aspx

Therefore we use a list of the most common and useful key names with an eye on
origin and license related information and return a value when there is one
present.
"""


"""
list of common info keys found in PE.
"""
PE_INFO_KEYS = (
                 u'APIVersion',
                 u'Assembly Version',
#                 u'BinType',
                 u'BuildDate',
#                 u'BuildType',
#                 u'BuildVariant',
                 u'BuildVersion',
                 u'Comments',
                 u'Company',
                 u'CompanyName',
#                 u'Configuration',
                 u'FileDescription',
                 u'FileVersion',
                 u'Full Version',
                 u'InternalName',
                 u'LegalCopyright',
                 u'LegalTrademarks',
                 u'LegalTrademarks1',
                 u'LegalTrademarks2',
#                 u'LibToolFileVersion',
                 u'License',
                 u'OriginalFilename',
                 u'ProductName',
                 u'ProductVersion',
#                 u'PrivateBuild',
#                 u'SharedMemoryVersion',
#                 u'SpecialBuild',
                 u'WWW',
                 )

PE_INFO_KEYSET = set(PE_INFO_KEYS)


def info(location, include_extra_data=False):
    """
    Return a dictionary of key/values for common "version" information
    available for a Windows dll or exe PE (portable executable).

    Return None for non windows PE executables.
    Return an empty dictionary for PE from which we could not collect data.
    If include_extra_data is True, also collect extra data found if any, returned
    as a dictionary under the 'extra_data' key in the returned dict.
    """
    if not location:
        return {}

    T = contenttype.get_type(location)

    if not T.is_winexe:
        return {}
    # we initialize a dir with empty values, as we must always return something
    # for all values
    peinf = OrderedDict([(k, u'',) for k in PE_INFO_KEYS] + [('extra_data',{},)])

    try:
        with closing(pefile.PE(location)) as pe:
            if not hasattr(pe, 'FileInfo'):
                # No fileinfo section: we return just empties
                return peinf

            sfi = [x for x in pe.FileInfo if x.name == 'StringFileInfo']

            if not sfi:
                # No stringfileinfo section: we return just empties
                return peinf

            try:
                strtab = sfi[0].StringTable[0]
            except Exception, e:
                # TODO: we may have no stringtable, return empties
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug('info: Failed to collect infos: ' + repr(e))
                return peinf

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('info: Entries keys: ' + str(set(k for k in strtab.entries)))
                logger.debug('info: Entry values:')
                for k, v in strtab.entries.items():
                    logger.debug('  ' + str(k) + ': ' + repr(v))

            for k, v in strtab.entries.items():
                    try:
                        # convert unicode to a safe ASCII representation
                        value = unicode(text.toascii(v).strip())
                        if k in PE_INFO_KEYSET:
                            peinf[k] = value
                        else:
                            # collect extra_data if any:
                            peinf['extra_data'][k] = value
                    except KeyError:
                        pass
    except Exception, e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('info: Failed to collect infos: ' + repr(e))
        # FIXME: return empty for now: this is wrong
        pass
    return peinf
