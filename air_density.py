def air_density(Tair,Tdew,MSLP):
    #   Tair    : 2-metre air temperature in Kelvin degrees
    #   Tdew    : 2-metre dew point temperature in Kelvin degrees
    #   MSLP    : Mean Sea Level Pressure in hPa

    # Routine written by Oyvind Saetra, MET Norway.
    # Thermodynaic variables for moist air density calculations
    # This is based on Vaisala conversion formulas from:
    # http://www.vaisala.com/Vaisala%20Documents/Application%20notes/Humidity_Conversion_Formulas_B210973EN-F.pdf
    
    T0 = 273.15         # 0 deg Kelvin
    Tn = 240.7263       # Tripple point temperature 
    A = 6.116441        # Constant used in  in Vaisala formulation
    m = 7.591386        # Constant used in  in Vaisala formulation
    R_d = 286.9         # Partial pressure for dry air
    R_v = 461.4         # Partial Pressure for water vapor
    hPa = 100.          # conversion from Hpa to Pa

    # Calculate the air density from the Vaisala formula,
    # here pressure must be expressed in Pascal.
    # Dewpoint temperature must be in degree Celcius
    TC = Tair - T0
    TD = Tdew - T0
    P_vs = A*10.**(m*TC/(TC+Tn))
    arg=m*(TD/(TD + Tn) - TC/(TC + Tn))
    RH = 100*10**arg
    P_v = P_vs*RH/100
    P_d = MSLP*hPa - P_v
    rhoa =P_d/(R_d*Tair) + P_v/(R_v*Tair)

    return(rhoa,RH)
