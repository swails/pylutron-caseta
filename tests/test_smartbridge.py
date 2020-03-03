"""Tests to validate ssl interactions."""
import asyncio
import logging
import pytest

import pylutron_caseta.smartbridge as smartbridge
from pylutron_caseta import FAN_MEDIUM

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())


class Bridge:
    """A test harness around SmartBridge."""

    def __init__(self, event_loop):
        """Create a new Bridge in a disconnected state."""
        self.event_loop = event_loop
        self.connections = asyncio.Queue(loop=event_loop)
        self.reader = self.writer = None

        async def fake_connect():
            """Use by SmartBridge to connect to the test."""
            closed = asyncio.Event(loop=event_loop)
            reader = _FakeLeapReader(closed, event_loop)
            writer = _FakeLeapWriter(closed, event_loop)
            await self.connections.put((reader, writer))
            return (reader, writer)

        self.target = smartbridge.Smartbridge(fake_connect,
                                              loop=event_loop)

    async def initialize(self):
        """Perform the initial connection with SmartBridge."""
        connect_task = self.event_loop.create_task(self.target.connect())
        reader, writer = await self.connections.get()

        async def wait(coro):
            # abort if SmartBridge reports it has finished connecting early
            task = self.event_loop.create_task(coro)
            r = await asyncio.wait((connect_task, task),
                                   loop=self.event_loop,
                                   timeout=10,
                                   return_when=asyncio.FIRST_COMPLETED)
            done, pending = r
            assert len(done) > 0, "operation timed out"
            if len(done) == 1 and connect_task in done:
                raise connect_task.exception()
            result = await task
            return result

        await self._accept_connection(reader, writer, wait)
        await connect_task

        self.reader = reader
        self.writer = writer
        self.connections.task_done()

    async def _accept_connection(self, reader, writer, wait):
        """Accept a connection from SmartBridge (implementation)."""
        value = await wait(writer.queue.get())
        assert value == {
                "CommuniqueType": "ReadRequest",
                "Header": {"Url": "/device"}}
        writer.queue.task_done()
        await reader.write({
            "CommuniqueType": "ReadResponse", "Header": {
                "MessageBodyType": "MultipleDeviceDefinition",
                "StatusCode": "200 OK",
                "Url": "/device"},
            "Body": {
                "Devices": [{
                    "href": "/device/1",
                    "Name": "Smart Bridge",
                    "FullyQualifiedName": ["Smart Bridge"],
                    "Parent": {"href": "/project"},
                    "SerialNumber": 1234,
                    "ModelNumber": "L-BDG2-WH",
                    "DeviceType": "SmartBridge",
                    "RepeaterProperties": {"IsRepeater": True}
                }, {
                    "href": "/device/2",
                    "Name": "Lights",
                    "FullyQualifiedName": ["Hallway", "Lights"],
                    "Parent": {"href": "/project"},
                    "SerialNumber": 2345,
                    "ModelNumber": "PD-6WCL-XX",
                    "DeviceType": "WallDimmer",
                    "LocalZones": [{"href": "/zone/1"}],
                    "AssociatedArea": {"href": "/area/1"}
                }, {
                    "href": "/device/3",
                    "Name": "Fan",
                    "FullyQualifiedName": ["Hallway", "Fan"],
                    "Parent": {"href": "/project"},
                    "SerialNumber": 3456,
                    "ModelNumber": "PD-FSQN-XX",
                    "DeviceType": "CasetaFanSpeedController",
                    "LocalZones": [{"href": "/zone/2"}],
                    "AssociatedArea": {"href": "/area/1"}
                }, {'href': '/device/4',
                    'Name': 'Occupancy Sensor',
                    'FullyQualifiedName': ['Basement Storage Area',
                                           'Occupancy Sensor'],
                    'Parent': {'href': '/project'},
                    'SerialNumber': 4567,
                    'ModelNumber': 'LRF2-XXXXB-P-XX',
                    'DeviceType': 'RPSOccupancySensor',
                    'AssociatedArea': {'href': '/area/21'},
                    'OccupancySensors': [{'href': '/occupancysensor/2'}],
                    'LinkNodes': [{'href': '/device/4/linknode/53'}],
                    'DeviceRules': [{'href': '/devicerule/11'}]
                }, {'href': '/device/5',
                    'Name': 'Occupancy Sensor Door',
                    'FullyQualifiedName': ['Master Bathroom',
                                           'Occupancy Sensor Door'],
                    'Parent': {'href': '/project'},
                    'SerialNumber': 5678,
                    'ModelNumber': 'PD-VSENS-XX',
                    'DeviceType': 'RPSOccupancySensor',
                    'AssociatedArea': {'href': '/area/26'},
                    'OccupancySensors': [{'href': '/occupancysensor/3'}],
                    'LinkNodes': [{'href': '/device/5/linknode/55'}],
                    'DeviceRules': [{'href': '/devicerule/123'}]
                }, {'href': '/device/6',
                    'Name': 'Occupancy Sensor Tub',
                    'FullyQualifiedName': ['Master Bathroom',
                                           'Occupancy Sensor Tub'],
                    'Parent': {'href': '/project'},
                    'SerialNumber': 6789,
                    'ModelNumber': 'PD-OSENS-XX',
                    'DeviceType': 'RPSOccupancySensor',
                    'AssociatedArea': {'href': '/area/26'},
                    'OccupancySensors': [{'href': '/occupancysensor/4'}],
                    'LinkNodes': [{'href': '/device/6/linknode/56'}],
                    'DeviceRules': [{'href': '/devicerule/122'}]}]}})
        value = await wait(writer.queue.get())
        assert value == {
                "CommuniqueType": "ReadRequest",
                "Header": {"Url": "/virtualbutton"}}
        writer.queue.task_done()
        await reader.write({
            "CommuniqueType": "ReadResponse",
            "Header": {
                "MessageBodyType": "MultipleVirtualButtonDefinition",
                "StatusCode": "200 OK",
                "Url": "/virtualbutton"},
            "Body": {
                "VirtualButtons": [{
                    "href": "/virtualbutton/1",
                    "Name": "scene 1",
                    "ButtonNumber": 0,
                    "ProgrammingModel": {"href": "/programmingmodel/1"},
                    "Parent": {"href": "/project"},
                    "IsProgrammed": True
                }, {
                    "href": "/virtualbutton/2",
                    "Name": "Button 2",
                    "ButtonNumber": 1,
                    "ProgrammingModel": {"href": "/programmingmodel/2"},
                    "Parent": {"href": "/project"},
                    "IsProgrammed": False
                }, {
                    'href': '/vbutton/1',
                    'ButtonNumber': 1,
                    'ProgrammingModel': {'href': '/programmingmodel/200'},
                    'Parent': {'href': '/area/9'},
                    'IsProgrammed': True,
                    'Category': {'Type': 'LivingRoom', 'SubType': 'Bright'}
                }]}})
        requested_zones = []
        for _ in range(0, 2):
            value = await wait(writer.queue.get())
            assert value["CommuniqueType"] == "ReadRequest"
            requested_zones.append(value["Header"]["Url"])
            writer.queue.task_done()
        requested_zones.sort()
        assert requested_zones == ["/zone/1/status", "/zone/2/status"]

    async def disconnect(self, exception=None):
        """Disconnect SmartBridge."""
        await self.reader.end(exception)

    async def accept_connection(self):
        """Wait for SmartBridge to reconnect."""
        reader, writer = await self.connections.get()

        async def wait(coro):
            # nothing special
            result = await coro
            return result

        await self._accept_connection(reader, writer, wait)

        self.reader = reader
        self.writer = writer
        self.connections.task_done()


class _FakeLeapWriter:
    """A "Writer" which just puts messages onto a queue."""

    def __init__(self, closed, loop):
        self.queue = asyncio.Queue(loop=loop)
        self.closed = closed
        self._loop = loop

    def write(self, obj):
        self.queue.put_nowait(obj)

    async def drain(self):
        task = self._loop.create_task(self.queue.join())
        await asyncio.wait((self.closed.wait(), task),
                           loop=self._loop,
                           return_when=asyncio.FIRST_COMPLETED)

    def abort(self):
        self.closed.set()


class _FakeLeapReader:
    """A "Reader" which just pulls messages from a queue."""

    def __init__(self, closed, loop):
        self._loop = loop
        self.closed = closed
        self.queue = asyncio.Queue(loop=loop)
        self.exception_value = None
        self.eof = False

    def exception(self):
        return self.exception_value

    async def read(self):
        task = self._loop.create_task(self.queue.get())
        r = await asyncio.wait((self.closed.wait(), task),
                               loop=self._loop,
                               return_when=asyncio.FIRST_COMPLETED)
        done, pending = r
        if task not in done:
            return None

        action = await task
        self._loop.call_soon(self.queue.task_done)
        try:
            value = action()
        except Exception as exception:
            self.exception_value = exception
            self.eof = True
            raise
        else:
            if value is None:
                self.eof = True
            return value

    async def write(self, item):
        def action():
            return item
        await self.queue.put(action)

    def at_eof(self):
        return self.closed.is_set() or self.eof

    async def end(self, exception=None):
        if exception is None:
            await self.write(None)
        else:
            def action():
                raise exception
            await self.queue.put(action)


@pytest.yield_fixture
def bridge(event_loop):
    """Create a bridge attached to a fake reader and writer."""
    harness = Bridge(event_loop)

    event_loop.run_until_complete(harness.initialize())

    yield harness

    event_loop.run_until_complete(harness.target.close())


@pytest.mark.asyncio
async def test_notifications(event_loop, bridge):
    """Test notifications are sent to subscribers."""
    notified = False

    def callback():
        nonlocal notified
        notified = True

    bridge.target.add_subscriber('2', callback)
    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/1/status"},
        "Body": {
            "ZoneStatus": {
                "Level": 100,
                "Zone": {"href": "/zone/1"}}}})
    await asyncio.wait_for(bridge.reader.queue.join(),
                           10, loop=event_loop)
    assert notified


@pytest.mark.asyncio
async def test_device_list(event_loop, bridge):
    """Test methods getting devices."""
    devices = bridge.target.get_devices()
    expected_devices = {
        "1": {
            "device_id": "1",
            "name": "Smart Bridge",
            "type": "SmartBridge",
            "zone": None,
            "current_state": -1,
            "fan_speed": None,
            "model": "L-BDG2-WH",
            "serial": 1234},
        "2": {
            "device_id": "2",
            "name": "Hallway_Lights",
            "type": "WallDimmer",
            "zone": "1",
            "model": "PD-6WCL-XX",
            "serial": 2345,
            "current_state": -1,
            "fan_speed": None},
        "3": {
            "device_id": "3",
            "name": "Hallway_Fan",
            "type": "CasetaFanSpeedController",
            "zone": "2",
            "model": "PD-FSQN-XX",
            "serial": 3456,
            "current_state": -1,
            "fan_speed": None},
        "4": {
            "device_id": "4",
            "name": "Basement Storage Area_Occupancy Sensor",
            "type": "RPSOccupancySensor",
            "model": "LRF2-XXXXB-P-XX",
            "serial": 4567,
            "current_state": -1,
            "fan_speed": None,
            "zone": None},
        "5": {
            "device_id": "5",
            "name": "Master Bathroom_Occupancy Sensor Door",
            "type": "RPSOccupancySensor",
            "model": "PD-VSENS-XX",
            "serial": 5678,
            "current_state": -1,
            "fan_speed": None,
            "zone": None},
        "6": {
            "device_id": "6",
            "name": "Master Bathroom_Occupancy Sensor Tub",
            "type": "RPSOccupancySensor",
            "model": "PD-OSENS-XX",
            "serial": 6789,
            "current_state": -1,
            "fan_speed": None,
            "zone": None},
    }

    assert devices == expected_devices

    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/1/status"},
        "Body": {
            "ZoneStatus": {
                "Level": 100,
                "Zone": {"href": "/zone/1"}}}})
    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/2/status"},
        "Body": {
            "ZoneStatus": {
                "FanSpeed": "Medium",
                "Zone": {"href": "/zone/2"}}}})
    await asyncio.wait_for(bridge.reader.queue.join(),
                           10, loop=event_loop)
    devices = bridge.target.get_devices()
    assert devices['2']['current_state'] == 100
    assert devices['2']['fan_speed'] is None
    assert devices['3']['current_state'] == -1
    assert devices['3']['fan_speed'] == FAN_MEDIUM

    devices = bridge.target.get_devices_by_domain('light')
    assert len(devices) == 1
    assert devices[0]['device_id'] == '2'

    devices = bridge.target.get_devices_by_type('WallDimmer')
    assert len(devices) == 1
    assert devices[0]['device_id'] == '2'

    devices = bridge.target.get_devices_by_types(('SmartBridge',
                                                  'WallDimmer'))
    assert len(devices) == 2

    device = bridge.target.get_device_by_id('2')
    assert device['device_id'] == '2'

    devices = bridge.target.get_devices_by_domain('fan')
    assert len(devices) == 1
    assert devices[0]['device_id'] == '3'

    devices = bridge.target.get_devices_by_type('CasetaFanSpeedController')
    assert len(devices) == 1
    assert devices[0]['device_id'] == '3'


def test_scene_list(bridge):
    """Test methods getting scenes."""
    scenes = bridge.target.get_scenes()
    assert scenes == {
        "1": {
            "scene_id": "1",
            "name": "scene 1"}}
    scene = bridge.target.get_scene_by_id('1')
    assert scene == {
        "scene_id": "1",
        "name": "scene 1"}


def test_is_connected(event_loop, bridge):
    """Test the is_connected method returns connection state."""
    assert bridge.target.is_connected() is True

    other = smartbridge.Smartbridge(None, loop=event_loop)
    assert other.is_connected() is False


@pytest.mark.asyncio
async def test_is_on(event_loop, bridge):
    """Test the is_on method returns device state."""
    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/1/status"},
        "Body": {
            "ZoneStatus": {
                "Level": 50,
                "Zone": {"href": "/zone/1"}}}})
    await asyncio.wait_for(bridge.reader.queue.join(),
                           10, loop=event_loop)
    assert bridge.target.is_on('2') is True

    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/1/status"},
        "Body": {
            "ZoneStatus": {
                "Level": 0,
                "Zone": {"href": "/zone/1"}}}})
    await asyncio.wait_for(bridge.reader.queue.join(), 10, loop=event_loop)
    assert bridge.target.is_on('2') is False


@pytest.mark.asyncio
async def test_is_on_fan(event_loop, bridge):
    """Test the is_on method returns device state for fans."""
    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/1/status"},
        "Body": {
            "ZoneStatus": {
                "FanSpeed": "Medium",
                "Zone": {"href": "/zone/1"}}}})
    await asyncio.wait_for(bridge.reader.queue.join(),
                           10, loop=event_loop)
    assert bridge.target.is_on('2') is True

    await bridge.reader.write({
        "CommuniqueType": "ReadResponse",
        "Header": {
            "MessageBodyType": "OneZoneStatus",
            "StatusCode": "200 OK",
            "Url": "/zone/1/status"},
        "Body": {
            "ZoneStatus": {
                "FanSpeed": "Off",
                "Zone": {"href": "/zone/1"}}}})
    await asyncio.wait_for(bridge.reader.queue.join(),
                           10, loop=event_loop)
    assert bridge.target.is_on('2') is False


@pytest.mark.asyncio
async def test_set_value(event_loop, bridge):
    """Test that setting values produces the right commands."""
    bridge.target.set_value('2', 50)
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command == {
        "CommuniqueType": "CreateRequest",
        "Header": {"Url": "/zone/1/commandprocessor"},
        "Body": {
            "Command": {
                "CommandType": "GoToLevel",
                "Parameter": [{"Type": "Level", "Value": 50}]}}}

    bridge.target.turn_on('2')
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command == {
        "CommuniqueType": "CreateRequest",
        "Header": {"Url": "/zone/1/commandprocessor"},
        "Body": {
            "Command": {
                "CommandType": "GoToLevel",
                "Parameter": [{"Type": "Level", "Value": 100}]}}}

    bridge.target.turn_off('2')
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command == {
        "CommuniqueType": "CreateRequest",
        "Header": {"Url": "/zone/1/commandprocessor"},
        "Body": {
            "Command": {
                "CommandType": "GoToLevel",
                "Parameter": [{"Type": "Level", "Value": 0}]}}}


@pytest.mark.asyncio
async def test_set_fan(event_loop, bridge):
    """Test that setting fan speed produces the right commands."""
    bridge.target.set_fan('2', FAN_MEDIUM)
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command == {
        "CommuniqueType": "CreateRequest",
        "Header": {"Url": "/zone/1/commandprocessor"},
        "Body": {
            "Command": {
                "CommandType": "GoToFanSpeed",
                "FanSpeedParameters": {"FanSpeed": "Medium"}}}}


@pytest.mark.asyncio
async def test_activate_scene(event_loop, bridge):
    """Test that activating scenes produces the right commands."""
    bridge.target.activate_scene('1')
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command == {
        "CommuniqueType": "CreateRequest",
        "Header": {
            "Url": "/virtualbutton/1/commandprocessor"},
        "Body": {"Command": {"CommandType": "PressAndRelease"}}}


@pytest.mark.asyncio
async def test_reconnect_eof(event_loop, bridge):
    """Test that SmartBridge can reconnect on disconnect."""
    await bridge.disconnect()
    await bridge.accept_connection()
    bridge.target.set_value('2', 50)
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command is not None


@pytest.mark.asyncio
async def test_reconnect_error(event_loop, bridge):
    """Test that SmartBridge can reconnect on error."""
    await bridge.disconnect()
    await bridge.accept_connection()
    bridge.target.set_value('2', 50)
    command = await asyncio.wait_for(bridge.writer.queue.get(),
                                     10, loop=event_loop)
    bridge.writer.queue.task_done()
    assert command is not None


@pytest.mark.asyncio
async def test_reconnect_timeout(event_loop):
    """Test that SmartBridge can reconnect if the remote does not respond."""
    bridge = Bridge(event_loop)

    time = 0.0

    def time_func():
        return time
    event_loop.time = time_func

    await bridge.initialize()

    time = smartbridge.PING_INTERVAL
    ping = await bridge.writer.queue.get()
    assert ping == {
        "CommuniqueType": "ReadRequest",
        "Header": {"Url": "/server/1/status/ping"}}

    time += smartbridge.PING_DELAY
    await bridge.accept_connection()

    bridge.target.set_value('2', 50)
    command = await bridge.writer.queue.get()
    bridge.writer.queue.task_done()
    assert command is not None

    await bridge.target.close()
