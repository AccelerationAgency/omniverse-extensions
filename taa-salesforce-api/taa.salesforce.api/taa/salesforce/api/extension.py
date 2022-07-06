import omni.ext
import omni.ui as ui
import omni.kit.commands
import requests
import json
from pxr import Gf

omni.kit.pipapi.install('simple_salesforce')

from simple_salesforce import Salesforce


class MyExtension(omni.ext.IExt):

    data = {'translate_x': 0, 'translate_y': 0, 'translate_z': 0}
    subscription = None
    stage = None
    salesforce = None  

    # lifecycle 


    def on_startup(self, ext_id):
        
        print("[taa.salesforce.api] Extension starting up")

        self.stage = omni.usd.get_context().get_stage()
         
        self._window = ui.Window("TAA Salesforce API", width=400, height=270)
                
        with self._window.frame:

            with ui.VStack():
        
                ui.Label('Consumer Key', height=20)
                self.consumer_key_field = ui.StringField(height=20)

                ui.Label('Consumer Secret', height=20)
                self.consumer_secret_field = ui.StringField(height=20)

                ui.Label('Username', height=20)
                self.username_field = ui.StringField(height=20)
                
                ui.Label('Password', height=20)
                self.password_field = ui.StringField(height=20)
                
                ui.Label('Organization Id', height=20)
                self.org_id_field = ui.StringField(height=20)

                ui.Label('Object Type', height=20)
                self.object_type_field = ui.StringField(height=20)

                ui.Label('Object Id', height=20)
                self.object_id_field = ui.StringField(height=20)

                ui.Spacer(height= 12)

                self.startButton = ui.Button("Start", height=54, clicked_fn=lambda: self.start(), style={"background_color": "green"})

                self.stopButton = ui.Button("Stop", height=54, clicked_fn=lambda: self.stop(), style={"color": "red"})

                ui.Spacer(height= 12)

                self.statusLabel = ui.Label('Click start to begin', height=14, style={"font_size": 12})


        self.stopButton.visible = False

        print("[taa.salesforce.api] Extension start up complete")


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

            print('changes applied successfully')
            
        except Exception as err:

            print(err)


    def read_config(self):
        try:
            
            consumer_key = self.consumer_key_field.model.get_value_as_string()            
            consumer_secret = self.consumer_secret_field.model.get_value_as_string()            
            username = self.username_field.model.get_value_as_string()
            password = self.password_field.model.get_value_as_string()            
            organization_id = self.org_id_field.model.get_value_as_string()           
            object_type = self.object_type_field.model.get_value_as_string()            
            object_id = self.object_id_field.model.get_value_as_string()

            return (consumer_key, consumer_secret, username, password, organization_id, object_type, object_id)
            
        except Exception as err:

            print(err)


    def read_data(self):
        try:

            consumer_key, consumer_secret, username, password, organization_id, object_type, object_id = self.read_config()

            if self.salesforce is None:
            
                payload = {
                    'grant_type': 'password',
                    'client_id': consumer_key,
                    'client_secret': consumer_secret,
                    'username': username,
                    'password': password,
                    'organizationId': organization_id
                }
                
                response = requests.post("https://login.salesforce.com/services/oauth2/token",
                                headers={"Content-Type": "application/x-www-form-urlencoded"},
                                data=payload)

                content = response.content.decode('UTF-8')
                body = json.loads(content)
                access_token = body.get('access_token')
                instance_url = body.get('instance_url')

                salesforce = Salesforce(session_id=access_token, instance_url=instance_url)

            response = salesforce.query("SELECT X__c, Y__c, Z__c FROM " + object_type + " WHERE Id ='" + object_id + "'")

            trackedObject = response['records'][0]

            if trackedObject is not None:

                # normalize and clean data

                self.data["translate_x"] = float(trackedObject.setdefault('X__c', 0)) * 100
                self.data["translate_y"] = float(trackedObject.setdefault('Y__c', 0)) * 100
                self.data["translate_z"] = float(trackedObject.setdefault('Z__c', 0)) * 100

                print(self.data)


        except Exception as err:

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