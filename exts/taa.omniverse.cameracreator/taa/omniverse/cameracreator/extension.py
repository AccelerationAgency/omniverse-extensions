import omni.ext
import omni.ui as ui
import omni.kit.commands as commands

class MyExtension(omni.ext.IExt):
    
    # Lifecycle 

    def on_startup(self, ext_id):
        print("[taa.omniverse.viewport] Extension starting up")

        self._window = ui.Window("TAA Quick Camera", width=200, height = 200)
        with self._window.frame:
            with ui.VStack(height = 0, spacing = 4):
                self.perspectiveButton = ui.Button("Perspective", height=40, clicked_fn=lambda: self.create_perspective_camera(), style={"background_color":"black"})
                self.topButton = ui.Button("Top", height=40, clicked_fn=lambda: self.create_top_camera(), style={"background_color":"black"})
                self.frontButton = ui.Button("Front", height=40, clicked_fn=lambda: self.create_front_camera(), style={"background_color":"black"})
                self.rightButton = ui.Button("Right", height=40, clicked_fn=lambda: self.create_right_camera(), style={"background_color":"black"})

        print("[taa.omniverse.viewport] Extension start up complete")

    def on_shutdown(self):
        print("[taa.omniverse.viewport] Extension shutting down")
        self.stop()
        print("[taa.omniverse.viewport] Extension shutdown complete")

    # Custom methods

    def set_camera(self, path):
        omni.kit.viewport_legacy.get_viewport_interface().get_viewport_window().set_active_camera(path)
        
    def rename_camera(self, name):
        cameraPath = omni.kit.viewport_legacy.get_viewport_interface().get_viewport_window().get_active_camera()
        omni.kit.commands.execute('MovePrims', paths_to_move={cameraPath: f'/World/Camera_{name}'})

    def create_perspective_camera(self):
        print("[taa.omniverse.viewport] Creating new perspective camera")
        self.set_camera("/OmniverseKit_Persp")
        commands.execute('DuplicateFromActiveViewportCameraCommand', viewport_name='Viewport')
        self.rename_camera("Perspective")

    def create_top_camera(self):
        print("[taa.omniverse.viewport] Creating new top-down camera")
        self.set_camera("/OmniverseKit_Top")
        commands.execute('DuplicateFromActiveViewportCameraCommand', viewport_name='Viewport')
        self.rename_camera("Top")

    def create_front_camera(self):
        print("[taa.omniverse.viewport] Creating new front view camera")
        self.set_camera("/OmniverseKit_Front")
        commands.execute('DuplicateFromActiveViewportCameraCommand', viewport_name='Viewport')
        self.rename_camera("Front")

    def create_right_camera(self):
        print("[taa.omniverse.viewport] Creating new right view camera")
        self.set_camera("/OmniverseKit_Right")
        commands.execute('DuplicateFromActiveViewportCameraCommand', viewport_name='Viewport')
        self.rename_camera("Right")

    def start(self):
        print("[taa.omniverse.viewport] Starting...")

    def stop(self):
        print("[taa.omniverse.viewport] Stopping...")
