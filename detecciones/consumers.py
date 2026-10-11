import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CameraStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer handling real-time camera video streaming and
    detection broadcasts between desktop capture clients and web dashboards.
    """

    async def connect(self):
        # Extract camera_id from URL route or default to CAM_01
        self.camera_id = self.scope['url_route']['kwargs'].get('camera_id', 'CAM_01')
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
            if msg_type in ('frame', 'camera_frame'):
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
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'detection_event',
                        'data': payload.get('data', payload),
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
