#transform define
def float_to_int(input_str):
    """
    output must be str
    """
    return str(int(float(input_str)))

def merge_val(input_str):
    """
    output must be str
    make val >= 10 to < 10
    split val to .0 .3 .6 .9
    """
    val = float(input_str)
    if val > 9.9: val = 9.9
    val = str(val)
    k, v = val.split(".")
    tmp = int(v)//3*3
    val = k + "." + str(tmp)
    return val

#filter define
def filt_some(input_str):
    """
    filter output must be bool
    """
    input_str = str(input_str)
    val = float(input_str)
    if val > 9.9: val = 9.9
    val = str(val)
    k, v = val.split(".")
    tmp = int(v)//3*3
    val = k + "." + str(tmp)
    if input_str == val:
        return True
    return False
    
if __name__ == "__main__":
    #print(merge_val(3.2))
    print(filt_some(3.3))
    print(filt_some(3.0))
    print(filt_some(3.1))
