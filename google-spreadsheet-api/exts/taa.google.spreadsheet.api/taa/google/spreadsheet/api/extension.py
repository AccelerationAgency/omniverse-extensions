import omni.ext
import omni.ui as ui
import omni.kit.commands

omni.kit.pipapi.install('google-api-python-client')
omni.kit.pipapi.install('google-auth-httplib2')

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pxr import Gf

class MyExtension(omni.ext.IExt):

    data = {'translate_x': 0, 'translate_y': 0, 'translate_z': 0, 'scale_x': 0, 'rotate_y': 0, 'rotate_z': 0, 'scale_x': 0, 'scale_y': 0, 'scale_z': 0}
    subscription = None
    stage = None
    google_sheet = None

    # lifecycle


    def on_startup(self, ext_id):

        print("[taa.google.spreadsheet.api] Extension starting up")

        self.stage = omni.usd.get_context().get_stage()

        self._window = ui.Window("TAA", width=400, height=270)

        with self._window.frame:

            with ui.VStack():

                ui.Label('Spreadsheet ID', height=20)
                self.spreadsheet_id_field = ui.StringField(height=20)

                ui.Label('Range', height=20)
                self.range_field = ui.StringField(height=20)

                ui.Label('API Key', height=20)
                self.api_key_field = ui.StringField(height=20)

                ui.Spacer(height= 12)

                self.startButton = ui.Button("Start", height=54, clicked_fn=lambda: self.start(), style={"background_color": "green"})

                self.stopButton = ui.Button("Stop", height=54, clicked_fn=lambda: self.stop(), style={"color": "red"})

                ui.Spacer(height= 12)

                self.statusLabel = ui.Label('Click start to begin', height=14, style={"font_size": 12})


        self.stopButton.visible = False

        print("[taa.google.spreadsheet.api] Extension start up complete")


    def on_shutdown(self):

        print("Extension shutting down")

        self.stop()

        print("Extension shutdown complete")


    # custom methods


    def apply_changes(self, frame):
        try:

            # load the data from Google Spreadsheet ever few seconds; this API is rate limited

            frameNumber = int(frame.payload["SWHFrameNumber"])

            if(frameNumber % 180 != 0): return

            print('applying changes')

            self.read_data()

            # act on all selected prims

            paths = self.list_paths_of_selected_prims()

            for path in paths:

                # get reference to the prim on stage, making sure that it's valid

                prim = self.stage.GetPrimAtPath(path)

                if prim.IsValid() == False: continue

                # transform the prim based on the settings in the Google Spreadsheet

                self.move_prim(prim)

                self.rotate_prim(prim)

                self.scale_prim(prim)

            print('changes applied successfully')

        except Exception as err:

            print(err)


    def read_config(self):
        try:

            spreadsheetId = self.spreadsheet_id_field.model.get_value_as_string()
            range = self.range_field.model.get_value_as_string()
            api_key = self.api_key_field.model.get_value_as_string()

            return (spreadsheetId, range, api_key)

        except Exception as err:

            print(err)


    def read_data(self):
        try:

            spreadsheetId, range, api_key = self.read_config()

            if self.google_sheet == None:

                service = build('sheets', 'v4', developerKey=api_key)

                self.google_sheet = service.spreadsheets()

            result = self.google_sheet.values().get(spreadsheetId=spreadsheetId, range=range).execute()

            values = result.get('values', [])

            data = toJSON(values)

            # normalize and clean data

            self.data["shape"] = data.setdefault('shape', 'Cube')
            self.data["size"] = float(data.setdefault('size', 100))
            self.data["radius"] = float(data.setdefault('radius', 100))
            self.data["translate_x"] = float(data.setdefault('translate_x', 0))
            self.data["translate_y"] = float(data.setdefault('translate_y', 0))
            self.data["translate_z"] = float(data.setdefault('translate_z', 0))
            self.data["rotate_x"] = float(data.setdefault('rotate_x', 0))
            self.data["rotate_y"] = float(data.setdefault('rotate_y', 0))
            self.data["rotate_z"] = float(data.setdefault('rotate_z', 0))
            self.data["scale_x"] = float(data.setdefault('scale_x', 1))
            self.data["scale_y"] = float(data.setdefault('scale_y', 1))
            self.data["scale_z"] = float(data.setdefault('scale_z', 1))

        except HttpError as err:

            print(err)


    def move_prim(self, prim):
        try:

            x = self.data.get('translate_x')
            y = self.data.get('translate_y')
            z = self.data.get('translate_z')

            omni.kit.commands.execute('TransformPrimSRT',
                path=prim.GetPath(),
                new_translation=Gf.Vec3d(x, y, z),
            )

        except Exception as err:

            print("Failed to move prim", err)


    def rotate_prim(self, prim):
        try:

            x = self.data.get('rotate_x')
            y = self.data.get('rotate_y')
            z = self.data.get('rotate_z')

            omni.kit.commands.execute('TransformPrimSRT',
                path=prim.GetPath(),
                new_rotation_euler=Gf.Vec3d(x, y, z),
            )

        except Exception as err:

            print("Failed to rotate prime", err)


    def scale_prim(self, prim):
        try:

            x = self.data.get('scale_x')
            y = self.data.get('scale_y')
            z = self.data.get('scale_z')

            omni.kit.commands.execute('TransformPrimSRT',
                path=prim.GetPath(),
                new_scale=Gf.Vec3d(x, y, z),
            )

        except Exception as err:

            print("Failed to scale prim", err)


    def list_paths_of_selected_prims(self):
        try:

            selection = omni.usd.get_context().get_selection()

            paths = selection.get_selected_prim_paths()

            return paths

        except Exception as err:

            print(err)


    def start(self):

        self.read_data()

        def on_update_apply(frame): self.apply_changes(frame)

        self.subscription = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(on_update_apply)

        self.startButton.visible = False

        self.stopButton.visible = True

        self.statusLabel.text = "Status: started"


    def stop(self):

        if self.subscription: del self.subscription

        self.startButton.visible = True

        self.stopButton.visible = False

        self.statusLabel.text = "Status: stopped"



"""
Utility functions
"""

def toJSON(values):

    json = {}

    if not values:
        return json

    for row in values:
        key = row[0]
        value = row[1]

        if not key or not value:
            continue

        json[row[0]] = row[1]

    return json