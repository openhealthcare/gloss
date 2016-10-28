GlossApi(Receiver, Importer, Subscribers, AysncSubscriber)

Receiver, can be a file, Hl7Message, and can return one or more results

etc

it receives the process message whereby it sends its contents to the importer
the importer

class GlossApi(object):
  def __init__(Receiver, importer, subscribers):
    self.Receiver = Receiver
    self.importer = importer
    self.subscriber = subscriber

    # the importer starts listening
    self.Importer.startListening().then(self.process_message)

  def process_message(self, inbound_message):
    result = self.importer(inbound_message)
    for subscriber in subscribers:
      subscribe(result)
