import os
import scipy
import numpy as np
from pyarbtools import error

BW_Mhz = 20
Gran = 2
MinLen = 60
bigEndian = True

def import_mat(filename, frame_interval_us):
    if not os.path.exists(filename):
        raise IOError("Invalid filename for import .mat file")
    _, ext = os.path.splitext(filename)
    if not ext == ".mat":
        raise IOError("File must be .mat extension")
    matdata = scipy.io.loadmat(filename)

    data_vars = []
    for key, value in matdata.items():
        if (key[:2] != "__" and key[-2:] != "__") and isinstance(value, np.ndarray) and value.size > 1:
            data_vars.append(key)

    if len(data_vars) == 1:
        var = data_vars[0]

        data = matdata[var]
        if data.shape[0] > 1:
            print("[WARN] NTX are set to 2, only generate path1!! Check NSS")
            data = data[0]
        data = data.flatten()
    else:
        raise error.WfmBuilderError("Too many data arrays in .mat file")
    
    data = np.concatenate([data, np.zeros(frame_interval_us * BW_Mhz * 2, dtype=data.dtype)])
    
    if len(data) % Gran != 0:
        data = np.concatenate([data, np.zeros(1, dtype=data.dtype)])

    if len(data) < MinLen:
        raise error.InstrumentError(f"Waveform length: {len(data)} must be at least {MinLen}")
    return data


def trans_wfm_iq(wfm):
    if bigEndian:
        return np.array(wfm * 32767 / 2047, dtype=np.int16).byteswap()
    else:
        return np.array(wfm * 32767 / 2047, dtype=np.int16)
    

def trans_wfm(wfm):
    max_val = np.max(np.max(wfm))
    if max_val < 1:
        wfm = wfm * 2047
        print("[debug]wave * 2047")
    elif max_val < 10:
        wfm = wfm * 443
        print("[debug]wave * 443")
    else:
        print("[debug]wave * 1")
    return trans_wfm_iq(np.real(wfm)), trans_wfm_iq(np.imag(wfm))


def gen_wfm(wfmData):
    if not isinstance(wfmData, np.ndarray):
        raise TypeError("wfmData should be a complex NumPy array.")

    # Waveform format checking. VSGs can only use 'iq' format waveforms.
    if wfmData.dtype != complex:
        raise TypeError("Invalid wfm type. IQ waveforms must be an array of complex values.")
    else:
        i, q = trans_wfm(wfmData)

        wfm_iq = np.empty(2*len(i), dtype=np.int16)
        wfm_iq[0::2] = i
        wfm_iq[1::2] = q

        return wfm_iq
    
if __name__ == "__main__":
    # file_path = "D:/wechat_doc/com_wechat_doc/WXWork/1688856744803585/Cache/File/2026-01/hesu_riu.mat"
    # file_path = r"D:\wechat_doc\com_wechat_doc\WXWork\1688856744803585\Cache\File\2026-01\waveform-0130\waveform-0130\hesu_160M_mcs0_txCore.mat"
    # file_path = r"D:\wechat_doc\com_wechat_doc\WXWork\1688856744803585\Cache\File\2026-01\waveform-0130\waveform-0130\hesu_DFEOut_sample320M.mat"
    # file_path = r"D:\wechat_doc\com_wechat_doc\WXWork\1688856744803585\Cache\File\2026-01\waveform-0130\waveform-0130\hesu_txcore_1.mat"
    # file_path = r"D:\wechat_doc\com_wechat_doc\WXWork\1688856744803585\Cache\File\2026-01\waveform-0130\waveform-0130\hesu_riu_1.mat"
    file_path = r"D:\wechat_doc\com_wechat_doc\WXWork\1688856744803585\Cache\File\2026-01\waveform-0130\waveform-0130\hesu_riu_2x_1.mat"
    BW_Mhz = 20

    data = import_mat(file_path, 30)
    wfm = gen_wfm(data)

    ############################generate or control play ###############################
    with open("./wave_gen/hesu_bw20m_sample40m_mcs0_riu2x_0130.WAVEFORM", 'wb') as f:
        f.write(wfm.tobytes())

    print("Generate wave over")

    # vsg = pyarbtools.instruments.VSG("192.168.1.100", timeout=3, reset=True)
    # vsg.configure(cf=200e6, fs=BW_Mhz*2e6, rfState=1, amp=-4)
    # vsg.download_wfm(wfm, wfmID="wfmID")
    # vsg.play(wfmID="wfmID")
    # vsg.stop()


