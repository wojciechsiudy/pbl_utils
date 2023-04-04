import math

MAX_UWB_OFFSET_FACTOR: float = 1.15

def angle_calculation(distance_l: float, distance_r: float, cross_used_distance:float):
    """
    distance_l -distance to left module
    distance_r -distance to right module
    use_length - 1 to use cross lenght 0 to use width
    """
    cross_used_distance= 0.0
    scale_offset_factor = 1.005


    if(distance_l + cross_used_distance <= distance_r or distance_r + cross_used_distance <= distance_l):
        #'''
        while(scale_offset_factor < MAX_UWB_OFFSET_FACTOR and (distance_l + cross_used_distance <= distance_r 
                                                               or distance_r + cross_used_distance <= distance_l)):
            if(distance_l + cross_used_distance <= distance_r):
                distance_l*=scale_offset_factor
                print(distance_l)
            if(distance_r + cross_used_distance <= distance_l):
                distance_r*=scale_offset_factor
                print(distance_r)
            scale_offset_factor += 0.005
        #'''
   
    if(distance_l + cross_used_distance <= distance_r or distance_r + cross_used_distance <= distance_l):
        return 420.0
    cos_a = (-cross_used_distance**2+distance_l**2+distance_r**2)/(2*distance_l*distance_r)
    rads = math.acos(cos_a) #wynik w radianach
    degrees = math.degrees(rads) #wynik w stopniach
    return (rads, degrees)




