# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 10:47:36 2021

@author: tzwn
"""

import pandas as pd

GNAF_PATH = "GNAF/"

pd.set_option('display.max_columns', None)

adr_detail = pd.read_csv("{}WA_ADDRESS_DETAIL_psv.psv".format(GNAF_PATH), sep="|")
adr_geo_code = pd.read_csv("{}WA_ADDRESS_DEFAULT_GEOCODE_psv.psv".format(GNAF_PATH), sep="|")
adr_local_street = pd.read_csv("{}WA_STREET_LOCALITY_psv.psv".format(GNAF_PATH), sep="|")

adr_detail.columns

adr_detail = adr_detail.set_index("ADDRESS_DETAIL_PID")
adr_geo_code = adr_geo_code.set_index("ADDRESS_DETAIL_PID")

df = adr_detail.join(adr_geo_code.drop(["DATE_CREATED", "DATE_RETIRED"], axis=1))


df.columns

cols = ['LOT_NUMBER_PREFIX', 'LOT_NUMBER', 'LOT_NUMBER_SUFFIX',
       'FLAT_TYPE_CODE', 'FLAT_NUMBER_PREFIX', 'FLAT_NUMBER',
       'FLAT_NUMBER_SUFFIX', 'LEVEL_TYPE_CODE', 'LEVEL_NUMBER_PREFIX',
       'LEVEL_NUMBER', 'LEVEL_NUMBER_SUFFIX', 'NUMBER_FIRST_PREFIX',
       'NUMBER_FIRST', 'NUMBER_FIRST_SUFFIX', 'NUMBER_LAST_PREFIX',
       'NUMBER_LAST', 'NUMBER_LAST_SUFFIX', 'POSTCODE', 'LONGITUDE',
       'LATITUDE', 'STREET_LOCALITY_PID']


local_street_cols = ['STREET_NAME', 'STREET_TYPE_CODE','STREET_SUFFIX_CODE', 'STREET_LOCALITY_PID']
# join df and adr_local_street on STREET_LOCALITY_PID

adr_local_street_by_streetid = adr_local_street[local_street_cols].set_index("STREET_LOCALITY_PID")
df_by_streetid = df[cols].set_index("STREET_LOCALITY_PID")

df2 = adr_local_street_by_streetid.join(df_by_streetid)
df2.drop_duplicates().to_csv("{}address_longlat.csv",format(GNAF_PATH))

