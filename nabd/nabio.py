import abc
import asyncio
from .choreography import ChoreographyInterpreter

class NabIO(object, metaclass=abc.ABCMeta):
  """ Interface for I/O interactions with a nabaztag """

  @abc.abstractmethod
  async def setup_ears(self, left_ear, right_ear):
    """
    Init ears and move them to the initial position.
    """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  async def move_ears(self, left_ear, right_ear):
    """
    Move ears to a given position and return only when they reached this
    position.
    """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  async def detect_ears_positions(self):
    """
    Detect ears positions and return the position before the detection.
    A second call will return the current position.
    """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  def set_leds(self, nose, left, center, right, bottom):
    """ Set the leds. None means to turn them off. """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  def pulse(self, led, color):
    """ Set a led to pulse. """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  def bind_button_event(self, loop, callback):
    """
    Define the callback for button events.
    callback is cb(event_type, time) with event_type being:
    - 'down'
    - 'up'
    - 'long_down'
    - 'double_click'
    - 'click_and_hold'

    Make sure the callback is called on the provided event loop, with loop.call_soon_threadsafe
    """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  def bind_ears_event(self, loop, callback):
    """
    Define the callback for ears events.
    callback is cb(ear) ear being the ear moved.

    Make sure the callback is called on the provided event loop, with loop.call_soon_threadsafe
    """
    raise NotImplementedError( 'Should have implemented' )

  @abc.abstractmethod
  async def play_info(self, tempo, colors):
    """
    Play an info animation.
    tempo & colors are as described in the nabd protocol.
    Run the animation once and returns.

    If 'left'/'center'/'right'/'bottom'/'nose' slots are absent, the light is off.
    """
    raise NotImplementedError( 'Should have implemented' )

  async def play_message(self, signature, body):
    """
    Play a message, i.e. a signature, a body and a signature.
    """
    preloaded_sig = await self._preload([signature])
    preloaded_body = await self._preload(body)
    ci = ChoreographyInterpreter(self.leds, self.ears, self.sound)
    await self._play_preloaded(ci, preloaded_sig, ChoreographyInterpreter.STREAMING_URN)
    await self._play_preloaded(ci, preloaded_body, ChoreographyInterpreter.STREAMING_URN)
    await self._play_preloaded(ci, preloaded_sig, ChoreographyInterpreter.STREAMING_URN)
    await ci.stop()

  async def play_sequence(self, sequence):
    """
    Play a simple sequence
    """
    preloaded = await self._preload(sequence)
    ci = ChoreographyInterpreter(self.leds, self.ears, self.sound)
    played_audio = await self._play_preloaded(ci, preloaded, None)
    if played_audio:
      await ci.stop()
    else:
      await ci.wait_until_complete()

  async def _play_preloaded(self, ci, preloaded, default_chor):
    for seq_item in preloaded:
      if 'choreography' in seq_item:
        chor = seq_item['choreography']
      else:
        chor = default_chor
      if chor != None:
        await ci.start(chor)
      else:
        await ci.stop()
      if 'audio' in seq_item:
        await self.sound.play_list(seq_item['audio'], True)
        return True
      else:
        return False

  async def _preload(self, sequence):
    preloaded_sequence = []
    for seq_item in sequence:
      if 'audio' in seq_item:
        preloaded_audio_list = []
        if isinstance(seq_item['audio'], str):
          print('Warning: audio should be a list of resources (sequence item: {seq_item})'.format(seq_item=seq_item))
          audio_list = [seq_item['audio']]
        else:
          audio_list = seq_item['audio']
        for res in audio_list:
          f = await self.sound.preload(res)
          if f != None:
            preloaded_audio_list.append(f)
        seq_item['audio'] = preloaded_audio_list
      preloaded_sequence.append(seq_item)
    return preloaded_sequence

  @abc.abstractmethod
  def cancel(self):
    """
    Cancel currently running sequence or info animation.
    """
    raise NotImplementedError( 'Should have implemented' )
