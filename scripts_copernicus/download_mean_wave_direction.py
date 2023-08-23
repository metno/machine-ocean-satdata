import os
import pickle
import cdsapi

data_dir = '/lustre/storeB/project/IT/geout/machine-ocean/data_raw/era5_buoys/'

# Load dict with buoy locations
with open( '../notebooks/in_situ_obs.pickle', 'rb') as handle:
    in_situ_dict = pickle.load(handle)

variables =  [
                #'mean_direction_of_total_swell', 
                'mean_direction_of_wind_waves', 'mean_wave_direction',
                'mean_wave_direction_of_first_swell_partition', 'mean_wave_direction_of_second_swell_partition', 'mean_wave_direction_of_third_swell_partition',
            ]
for var in variables:
    for buoy in in_situ_dict:
        path = data_dir +'/mean_wave_direction/era_' + var + '_' + buoy + '.nc'
        if not os.path.exists(path):
            lat = in_situ_dict[buoy]['lat'][0]
            lon = in_situ_dict[buoy]['lon'][0]
            north = lat + 5
            south = lat - 5
            east = lon + 5
            west = lon - 5

            c = cdsapi.Client()
            c.retrieve(
                'reanalysis-era5-single-levels',
                {
                'product_type':'reanalysis',
                'format':'netcdf',
                'variable':var,
                'area'    : [north, west, south, east],
                'year':[
                    #'1979', '1980', '1981',
                    #'1982', '1983', '1984',
                    #'1985', '1986', '1987',
                    #'1988', '1989', '1990',
                    #'1991', '1992', '1993',
                    #'1994', '1995', '1996',
                    #'1997', '1998', '1999',
                    #'2000', '2001', '2002',
                    #'2003', '2004', '2005',
                    #'2006', '2007', '2008',
                    #'2009', '2010', '2011',
                    '2012', '2013', '2014',
                    '2015', '2016', '2017',
                    '2018', '2019', '2020'
                ],
                'month':[
                    "01", "02", "03", "04", "05", "06",
                    "07", "08", "09", "10", "11", "12"
                    ],
                'day':[
                    '01','02','03',
                    '04','05','06',
                    '07','08','09',
                    '10','11','12',
                    '13','14','15',
                    '16','17','18',
                    '19','20','21',
                    '22','23','24',
                    '25','26','27',
                    '28','29','30',
                    '31'
                ],
                'time':[
                    '00:00','01:00','02:00',
                    '03:00','04:00','05:00',
                    '06:00','07:00','08:00',
                    '09:00','10:00','11:00',
                    '12:00','13:00','14:00',
                    '15:00','16:00','17:00',
                    '18:00','19:00','20:00',
                    '21:00','22:00','23:00'
                ]
                },

                path)
        else:
            print(path + ' already exists.')





