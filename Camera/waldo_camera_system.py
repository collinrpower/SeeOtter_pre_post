from Camera.camera import Camera
from Camera.camera_calibration import CameraCalibration
from Camera.camera_system import CameraSystem
from Utilities.json_convert import JsonConvert
from config import *


@JsonConvert.register
class WaldoCameraSystem(CameraSystem):

    def __init__(self, name="Single Camera System", cameras=None):
        camera = Camera(
            "Any Camera",
            image_regex="",
            rotate_image=False,
            orientation=CameraCalibration(
                angle_x=0,
                angle_y=0,
                angle_z=0,
                hfov=WALDO_HORIZONTAL_FOV
            )
        )
        super().__init__(name=name, cameras=[camera])
