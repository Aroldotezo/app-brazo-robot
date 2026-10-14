import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class CameraStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer handling real-time camera video streaming and
    detection broadcasts between desktop capture clients and web dashboards.
    """

    async def connect(self):
        # Extract camera_id from URL route or default to CAM_01 (normalized to uppercase)
        self.camera_id = (self.scope['url_route']['kwargs'].get('camera_id') or 'CAM_01').upper()
        self.room_group_name = f"camera_{self.camera_id}"
        self.global_group_name = "camera_all"

        # Join room group for this camera and global feed
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.global_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial connection confirmation to client
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'camera_id': self.camera_id,
            'message': 'Connected to camera stream channel'
        }))

    async def disconnect(self, close_code):
        # Leave room groups on disconnect
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.global_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming messages from desktop capture app or browser clients.
        Supports both binary JPEG frames and JSON text messages (base64, events).
        """
        # Handle binary JPEG frame payload
        if bytes_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'camera_frame_binary',
                    'bytes': bytes_data,
                    'sender_channel': self.channel_name
                }
            )
            return

        # Handle JSON formatted message payload
        if text_data:
            try:
                payload = json.loads(text_data)
            except json.JSONDecodeError:
                return

            msg_type = payload.get('type', '')

            # Heartbeat ping/pong
            if msg_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                return

            # Camera video frame (base64 image or stream metadata)
            # Fully supports video_frame, frame, camera_frame and direct image payloads
            if (
                msg_type in ('video_frame', 'frame', 'camera_frame', 'stream_frame', 'camera_feed', 'image')
                or 'frame' in payload
                or 'image' in payload
            ):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'camera_frame_text',
                        'data': payload,
                        'sender_channel': self.channel_name
                    }
                )
                return

            # Detection event broadcast from desktop
            if msg_type == 'detection':
                raw_data = payload.get('data', payload)
                saved_data = await self.persist_detection_event(raw_data)

                # Broadcast to camera room and global camera room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'detection_event',
                        'data': saved_data,
                        'sender_channel': self.channel_name
                    }
                )
                await self.channel_layer.group_send(
                    self.global_group_name,
                    {
                        'type': 'detection_event',
                        'data': saved_data,
                        'sender_channel': self.channel_name
                    }
                )
                return

            # Forward any other custom message type to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'camera_frame_text',
                    'data': payload,
                    'sender_channel': self.channel_name
                }
            )

    # Group message handlers
    async def camera_frame_binary(self, event):
        """Send raw binary frame to receiving clients (skipping sender)."""
        if event.get('sender_channel') != self.channel_name:
            await self.send(bytes_data=event['bytes'])

    async def camera_frame_text(self, event):
        """Send JSON text frame to receiving clients (skipping sender)."""
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps(event['data']))

    async def detection_event(self, event):
        """Broadcast new detection event to all connected dashboard clients."""
        await self.send(text_data=json.dumps({
            'type': 'detection',
            'data': event['data']
        }))

    async def system_notification(self, event):
        """Broadcast system alert or toast notification message."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event.get('notification_type', 'info'),
            'message': event.get('message', '')
        }))

    @database_sync_to_async
    def persist_detection_event(self, data):
        """
        Persists a detection event received via WebSocket to the database
        if it has not already been persisted (i.e. does not have an 'id').
        Handles optional base64 image data.
        """
        if isinstance(data, dict) and data.get('id'):
            return data

        import base64
        import uuid
        from django.core.files.base import ContentFile
        from .models import Deteccion

        if not isinstance(data, dict):
            return data

        objeto = data.get('objeto', 'Objeto detectado')
        categoria = data.get('categoria', 'Inorgánico')
        confianza_val = data.get('confianza', 0.9)
        try:
            confianza = float(confianza_val)
        except (ValueError, TypeError):
            confianza = 0.9

        # Normalize confidence if sent as percentage (e.g. 95 -> 0.95)
        if 1.0 < confianza <= 100.0:
            confianza = round(confianza / 100.0, 4)

        camara_id = data.get('camara_id', self.camera_id)

        det = Deteccion(
            objeto=objeto,
            categoria=categoria,
            confianza=confianza,
            camara_id=camara_id,
        )

        b64_img = data.get('imagen_base64') or data.get('imagen')
        if isinstance(b64_img, str) and (';base64,' in b64_img or b64_img.startswith('data:')):
            try:
                ext = 'jpg'
                if ';base64,' in b64_img:
                    header, b64_data = b64_img.split(';base64,', 1)
                    if 'png' in header:
                        ext = 'png'
                else:
                    b64_data = b64_img
                decoded = base64.b64decode(b64_data)
                det.imagen.save(f"captura_{uuid.uuid4().hex[:10]}.{ext}", ContentFile(decoded), save=False)
            except Exception:
                pass

        det.save()

        return {
            'id': det.id,
            'objeto': det.objeto,
            'categoria': det.categoria,
            'confianza': det.confianza,
            'camara_id': det.camara_id,
            'imagen_url': det.imagen.url if det.imagen else None,
            'fecha_registro': det.fecha_registro.strftime('%d/%m/%Y %H:%M:%S'),
        }
