import omni.ext
import omni.ui as ui
import omni.kit.commands
import json

omni.kit.pipapi.install('stomp.py')

import stomp


class MyExtension(omni.ext.IExt):

    stage = None

    # lifecycle


    def on_startup(self, ext_id):

        print("[taa.gemini.telemetry] Extension starting up")

        self.stage = omni.usd.get_context().get_stage()

        self._window = ui.Window("TAA", width=400, height=150)

        with self._window.frame:

            with ui.VStack():

                self.startButton = ui.Button("Start", height=54, clicked_fn=lambda: self.start(), style={"background_color": "green"})

                self.stopButton = ui.Button("Stop", height=54, clicked_fn=lambda: self.stop(), style={"color": "red"})

                ui.Spacer(height= 12)

                self.statusLabel = ui.Label('Click start to begin', height=14, style={"font_size": 12})


        self.stopButton.visible = False

        self.conn = stomp.Connection([('rabbitmq.taa.io', 61613)], vhost='gemini', heartbeats=(4000, 4000))

        self.conn.set_listener('', self.MyListener(self.conn, self.apply_changes))

        print("[taa.gemini.telemetry] Extension start up complete")


    def on_shutdown(self):

        print("Extension shutting down")

        self.stop()

        self.conn.disconnect()

        print("Extension shutdown complete")


    # custom methods


    def apply_changes(self, coords):
        try:

            print('applying changes', coords)

            coords = json.loads(coords)

            coords['x'] = coords.setdefault("x", 0) * 100
            coords['y'] = coords.setdefault("y", 0) * 100
            coords['z'] = coords.setdefault("z", 0) * 100

            print(coords)

            # act on all selected prims

            paths = self.list_paths_of_selected_prims()

            return

            for path in paths:

                # get reference to the prim on stage, making sure that it's valid

                prim = self.stage.GetPrimAtPath(path)

                if prim.IsValid() == False: continue

                # transform the prim based on the settings in the Google Spreadsheet

                # self.move_prim(prim, coords)

            print('changes applied successfully')

        except Exception as err:

            print(err)


    def connect_and_subscribe(self, conn):
        
        conn.connect('appuser', 'NW6BuyVm37qJ', wait=True)
        
        conn.subscribe(destination='/exchange/telemetry-exchange', id=1, ack='auto')

        print('connected to rabbitmq.taa.ia')


    def read_config(self):
        try:

            spreadsheetId = self.spreadsheet_id_field.model.get_value_as_string()
            range = self.range_field.model.get_value_as_string()
            api_key = self.api_key_field.model.get_value_as_string()

            return (spreadsheetId, range, api_key)

        except Exception as err:

            print(err)


    def move_prim(self, prim, coords):
        try:

            x = coords.get('translate_x')
            y = coords.get('translate_y')
            z = coords.get('translate_z')

            omni.kit.commands.execute('TransformPrimSRT',
                path=prim.GetPath(),
                new_translation=Gf.Vec3d(x, y, z),
            )

        except Exception as err:

            print("Failed to move prim", err)


    def list_paths_of_selected_prims(self):
        try:

            selection = omni.usd.get_context().get_selection()

            paths = selection.get_selected_prim_paths()

            return paths

        except Exception as err:

            print(err)


    def start(self):

        self.connect_and_subscribe(self.conn)

        self.startButton.visible = False

        self.stopButton.visible = True

        self.statusLabel.text = "Status: started"


    def stop(self):

        self.startButton.visible = True

        self.stopButton.visible = False

        self.statusLabel.text = "Status: stopped"


    class MyListener(stomp.ConnectionListener):
        def __init__(self, conn, fn):
            self.conn = conn
            self.fn = fn

        def on_error(self, frame):
            print('received an error "%s"' % frame.body)

        def on_message(self, frame):
            print('received a message "%s"' % frame.body)
            self.fn(frame.body)
           
        def on_disconnected(self):
            print('disconnected')
            self.connect_and_subscribe(self.conn)