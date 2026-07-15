"""Listar y cambiar el dispositivo de salida de audio por defecto en Windows.

Usa la interfaz COM no documentada IPolicyConfig (la misma que usa el panel
de sonido de Windows por debajo). Requiere pip install pycaw comtypes.
"""

from ctypes import HRESULT, c_int, c_wchar_p

from comtypes import COMMETHOD, CLSCTX_ALL, GUID, CoCreateInstance, IUnknown
from pycaw.pycaw import AudioUtilities

CLSID_PolicyConfigClient = GUID("{870AF99C-171D-4F9E-AF0D-E63DF40C2BC9}")
IID_IPolicyConfig = GUID("{F8679F50-850A-41CF-9C72-430F290290C8}")

ROLES = (0, 1, 2)  # eConsole, eMultimedia, eCommunications


class IPolicyConfig(IUnknown):
    _iid_ = IID_IPolicyConfig
    _methods_ = [
        COMMETHOD([], HRESULT, "GetMixFormat"),
        COMMETHOD([], HRESULT, "GetDeviceFormat"),
        COMMETHOD([], HRESULT, "ResetDeviceFormat"),
        COMMETHOD([], HRESULT, "SetDeviceFormat"),
        COMMETHOD([], HRESULT, "GetProcessingPeriod"),
        COMMETHOD([], HRESULT, "SetProcessingPeriod"),
        COMMETHOD([], HRESULT, "GetShareMode"),
        COMMETHOD([], HRESULT, "SetShareMode"),
        COMMETHOD([], HRESULT, "GetPropertyValue"),
        COMMETHOD([], HRESULT, "SetPropertyValue"),
        COMMETHOD(
            [],
            HRESULT,
            "SetDefaultEndpoint",
            (["in"], c_wchar_p, "wszDeviceId"),
            (["in"], c_int, "eRole"),
        ),
        COMMETHOD([], HRESULT, "SetEndpointVisibility"),
    ]


def list_active_devices():
    return [d.FriendlyName for d in AudioUtilities.GetAllDevices() if str(d.state) == "AudioDeviceState.Active"]


def get_current_device_name():
    return AudioUtilities.GetSpeakers().FriendlyName


def set_default_device(name):
    """Busca (sin importar mayusculas/parcial) un dispositivo activo por nombre y lo pone por defecto."""
    devices = [d for d in AudioUtilities.GetAllDevices() if str(d.state) == "AudioDeviceState.Active"]
    for device in devices:
        if name.lower() in device.FriendlyName.lower():
            policy_config = CoCreateInstance(CLSID_PolicyConfigClient, IPolicyConfig, CLSCTX_ALL)
            for role in ROLES:
                policy_config.SetDefaultEndpoint(device.id, role)
            return device.FriendlyName
    return None
