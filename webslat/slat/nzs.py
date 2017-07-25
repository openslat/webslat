def C_h(soil_class, T):
    if soil_class == "A" or soil_class == "B":
        if T == 0:
            return(1.0)
        elif T < 0.1:
            return(1.0 + 1.35 * (T/0.1))
        elif T <= 0.3:
            return(2.35)
        elif T <= 1.5:
            return(1.60 * (0.5 / T)**0.75)
        elif T <=3.0:
            return(1.05/T) 
        else:
            return(3.15/(T*T))
    elif soil_class == "C":
        if T == 0.0:
            return(1.33)
        elif T < 0.1:
            return(1.33 + 1.60*(T/0.1))
        elif T < 0.3:
            return(2.93)
        elif T < 1.5:
            return(2.0 * (0.5/T)**0.75)
        elif T < 3:
            return(1.32/T)
        else:
            return(3.96/T**2)
    elif soil_class == "D":
        if T == 0.0:
            return(1.12)
        elif T <= 0.1:
            return(1.12 + 1.88*(T/0.1))
        elif T < 0.56:
            return(3.0)
        elif T < 1.5:
            return(2.4 * (0.75/T)**0.75)
        elif T < 3:
            return(2.14/T)
        else:
            return(6.42/T**2)
    elif soil_class == "E":
        if T <= 0.0:
            return(1.12)
        elif T < 0.1:
            return(1.12 + 1.88*(T/0.1))
        elif T < 1.0:
            return(3.0)
        elif T < 1.5:
            return(3.0/T**0.75)
        elif T < 3:
            return(3.32/T)
        else:
            return(9.96/T**2)

def N_max(T) :
    if (T <= 1.5) :
        return(1.0)
    elif (T < 2) :
        return(1.0 + (1.12 - 1.0) * (T-1.5)/(2 - 1.5))
    elif (T < 3) :
        return(1.12 + (1.36 - 1.12) * (T-2)/(3 - 2))
    elif (T < 4) :
        return(1.36 + (1.60 - 1.36) * (T-3)/(4 - 3))
    elif (T < 5) :
        return(1.60 + (1.72 - 1.60) * (T-4)/(5 - 4))
    else :
        return(1.72)

def N(T, D, r) :
    if (r >= 1/250 or not(D)):
        return(1.0)
    elif (D <= 2) :
        return(N.max(T))
    elif (D > 20) :
        return(1.0)
    else :
        return(1 + (N.max(T) - 1) * (20 - D)/18)

def R(years):
    if years == 2500:
        return 1.8
    elif years == 2000:
        return 1.7
    elif years == 1000:
        return 1.3
    elif years == 500:
        return 1.0
    elif years == 250:
        return 0.75
    elif years == 100:
        return 0.5
    elif years == 50:
        return 0.35
    elif years == 25:
        return 0.25
    elif years == 20:
        return 0.20
    else:
        raise ValueError("R(years): years unknown [{}]".format(years))

R_defaults = [20, 25, 50, 100, 250, 500, 1000, 2000, 2500]

def C(soil_class, period, years, Z, distance):
    cht = C_h(soil_class, period)
    ntd = N(period, distance, years)
    return(cht*Z*R(years)*ntd)
    


 
