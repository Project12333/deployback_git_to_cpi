// Clear all existing attachments
message.getAttachments().clear()

// Now add only XML
def newAttachmentMap = [:]
newAttachmentMap.put("customerData.xml", dataHandler)
message.setAttachments(newAttachmentMap)
