import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
import groovy.json.*
import java.io.*;
import groovy.xml.XmlUtil;
import com.sap.it.api.ITApiFactory;
import com.sap.it.api.mapping.ValueMappingApi;
import java.text.DateFormat;  
import java.util.Calendar;  
import java.util.Date;  

def Message SetUngerboeckToken(Message message) {
        
	def body = message.getBody(java.lang.String) as String;
    def token = body.replaceAll(/"/,"") as String;
     
    message.setBody("");
    message.setHeader("Token", token);
     
    return message;
}




def Message ConvertJSON(Message message) {

    def jsonOP = message.getBody(String.class);
    
    jsonOP=jsonOP.toString()

    jsonOP=jsonOP.replaceAll(",\"\":\"\\s*(.*?)\\s*\"", "") //I-452536: remove json element without name
    jsonOP=jsonOP.replaceAll("\"\":\"\\s*(.*?)\\s*\",", "") //I-452536: remove first json element without name

    jsonOP = jsonOP.replaceAll("\\\\u[0-9][0-9][0-9][0-9]", ""); //remove unicode characters
    
    def json_to_str=jsonOP.substring(1, jsonOP.length()- 1);
    
    json_to_str="{\"Root\": [{\"Record\":["+json_to_str+"]}]}"
    
    json_to_str = json_to_str.replaceAll("<Record/>", "").trim(); 
    
    message.setBody(json_to_str);
    
    return message;
}



def Message RemoveMultimapTags(Message message) {
//Body

    def body = message.getBody(java.lang.String) as String; 
    
    body = body.replaceAll("<multimap:Messages xmlns:multimap=", ""); 
    
    body = body.replaceAll("\"http://sap.com/xi/XI/SplitAndMerge\">", ""); 
    
    body = body.replaceAll("<multimap:Message1>",""); 
    
    body = body.replaceAll("</multimap:Message1></multimap:Messages>", ""); 
    
    //Depends on your requirement, add this below line
     body = body.replaceAll("\\<\\?xml(.+?)\\?\\>", "").trim(); 
    
     body = body.replaceAll("<Record/>", "").trim(); 
    
    message.setBody(body); 
    
    return message; 

}




def Message RemoveMultimapRootTags(Message message) {
//Body

    def body = message.getBody(java.lang.String) as String; 

    body = body.replaceAll("<multimap:Messages xmlns:multimap=", ""); 
    
    body = body.replaceAll("\"http://sap.com/xi/XI/SplitAndMerge\">", ""); 
    
    body = body.replaceAll("<multimap:Message1>",""); 
    
    body = body.replaceAll("</multimap:Message1></multimap:Messages>", ""); 
    
    //Depends on your requirement, add this below line
     body = body.replaceAll("\\<\\?xml(.+?)\\?\\>", "").trim(); 
    
     body = body.replaceAll("<Root>", "").trim(); 
    
     body = body.replaceAll("</Root>", "").trim(); 
     body = body.replaceAll("<Root/>", "").trim(); 
     body = body.replaceAll("<Record/>", "").trim(); 
     
     
     body = body.replaceAll("<root>", "").trim(); 
    
     body = body.replaceAll("</root>", "").trim(); 
     body = body.replaceAll("<root/>", "").trim();       
     body = "<Root>" + body + "</Root>";
    
    message.setBody(body); 
    
    return message; 

}





def Message AppendCustomerInfo(Message message) { 
//Body
    def body = message.getBody(java.lang.String) as String;
    def customer_account = message.getProperty("Customer_Account") as String;
    def organization     = message.getProperty("Organization") as String;
  //  customer_account = customer_account.replaceAll(/0+(?!$)/, "");
    if( customer_account !="" || organization != ""){ 
    def customer_info = "<Customer><CustomerNo>" + customer_account + "</CustomerNo><Organization>" + organization + "</Organization></Customer>";

    body = customer_info; 
    } else body = "";
    message.setBody(body); 


    return message; 

}


def Message RemoveDuplicateRecords(Message message) {

    def body = message.getBody(java.lang.String) as String;
   
    def body_split      = body.split("<Customer>");
    def body_split_copy = body_split;
    def counter = 0;
    for( String value_ref : body_split )
      {
          counter = 0;
          for( String value_lookup : body_split_copy )
          {
              if(value_ref == value_lookup) counter = counter + 1;
              
          }
          if(counter > 1){
              
             body = body.replaceAll("<Customer>" + value_ref ,""); 
             body = body + "<Customer>" + value_ref;
          }
          
      }
      
    message.setBody(body);
    return message; 
}


def Message SetBusinessPartner(Message message) {
    def customer_account = message.getProperty("Customer_Account") as String;
    def organization     = message.getProperty("Organization") as String;
    customer_account = customer_account.replaceAll(/0+(?!$)/, "");
    if( customer_account !="" || organization != ""){ 
    
        
    message.setProperty("Business_Partner", organization + "-" + customer_account);
        
    } 

    return message; 

}



def Message SetPropertyInvoiceKey(Message message) {

    def body = message.getBody(java.lang.String) as String; 
    def root  = new XmlSlurper().parseText(body);
    def refid_query = '';
    
    root.Record.each { Record ->
      if (Record.InvoiceSearch != ''){
            if(refid_query == '') refid_query = "DocumentReferenceID eq '" + Record.InvoiceSearch + "'";
            else refid_query = refid_query +  "or DocumentReferenceID eq '" + Record.InvoiceSearch + "'";
        }
      }
    
    message.setProperty('Refid_Query', refid_query);
    return message; 

}



def Message GroupRegistrationOrders(Message message) {

    def body = message.getBody(java.lang.String) as String; 
    def root  = new XmlSlurper().parseText(body);
    
    def group = "";
    def key = "";
    
    root.Record.each { record -> 
            key = "<Item><OrganizationCode>" + record.OrganizationCode + "</OrganizationCode><OrderNumber>" + record.OrderNumber + "</OrderNumber><Invoice>" + record.Invoice + "</Invoice><Event>" + record.Event + "</Event><ChangedOn>" + record.ChangedOn + "</ChangedOn><Currency>" + record.Currency + "</Currency></Item>";
            if(group.indexOf(key) < 0) { 
                group += key;
            }
    }
    
    group = "<root>" + group + "</root>";
    
    
    
    def grouproot  = new XmlSlurper().parseText(group);
    def finalbody = "";
    
    
    
    grouproot.Item.each { Item ->
    
        def amountsum = 0;
    
        finalbody += "<Item><OrganizationCode>" + Item.OrganizationCode + "</OrganizationCode><OrderNumber>" + Item.OrderNumber + "</OrderNumber><Invoice>" + Item.Invoice + "</Invoice><Event>" + Item.Event + "</Event><ChangedOn>" + Item.ChangedOn + "</ChangedOn><Currency>" + Item.Currency + "</Currency><PONumber></PONumber>";
    
        root.Record.each { record -> 
        
            if( Item.OrganizationCode == record.OrganizationCode && 
                Item.OrderNumber == record.OrderNumber && 
                Item.Invoice == record.Invoice &&
                Item.Event == record.Event )
                
                //amountsum += record.ExtendedChrg.toDouble();
                //amountsum += record.TaxAmount.toDouble();
                finalbody += XmlUtil.serialize(record).replaceAll("\\<\\?xml(.+?)\\?\\>", "").trim();
           
           
            }
            
            
     
        finalbody += "<Amount>" + "" + "</Amount></Item>";
        
        
        }
    finalbody = "<root>" + finalbody + "</root>";    
    message.setBody(finalbody);
    return message; 


}


def Message GroupPurchaseOrders(Message message) {

    def body = message.getBody(java.lang.String) as String; 
    def root  = new XmlSlurper().parseText(body);
    
    def group = "";
    def key = "";
    
    root.Record.each { record -> 
            key = "<Item><Organization>" + record.Organization + "</Organization><Number>" + record.Number + "</Number><Supplier>" + record.Supplier + "</Supplier></Item>";
            if(group.indexOf(key) < 0) { 
                group += key;
            }
    }
    
    group = "<root>" + group + "</root>";
    
    
    def grouproot  = new XmlSlurper().parseText(group);
    def finalbody = "";
    
    
    
    grouproot.Item.each { Item ->
    
        def amountsum = 0;
    
        finalbody += "<Item><Organization>" + Item.Organization + "</Organization><Number>" + Item.Number + "</Number><Supplier>" + Item.Supplier + "</Supplier>";
    
        root.Record.each { record -> 
        
            if( Item.Organization == record.Organization && 
                Item.Number == record.Number )
                finalbody += XmlUtil.serialize(record).replaceAll("\\<\\?xml(.+?)\\?\\>", "").trim();
           
            }
            
     
        finalbody += "</Item>";
        
        
        }
    finalbody = "<root>" + finalbody + "</root>";    
    message.setBody(finalbody);
    return message; 
}





def Message RemoveJED(Message message) {
    def body = message.getBody(java.lang.String) as String; 
    def root  = new XmlSlurper().parseText(body);

    root.Record.each{ record -> 
            if( record.Source == 'PI'){
                
                root.Record.findAll{ it.Organization == record.Organization && it.Invoice == record.Invoice && it.EntryNumber.text().compareTo(record.EntryNumber.text()) == 1  }*.replaceNode{ };
                
            }
                           
            
        } 

    message.setBody( XmlUtil.serialize(root) ); 

    return message; 
    
}





def Message CollectGSIInvoices(Message message) {

    def body = message.getBody(java.lang.String) as String; 
    def root  = new XmlSlurper().parseText(body);
    
    def vm = ITApiFactory.getApi(ValueMappingApi.class, null)
    
    def refid_query = '';
    
  root.Item.each { Record ->
      if (Record.OrderNumber != ''){
            if(refid_query == '') refid_query = "( DocumentReferenceID eq 'INV " + Record.Invoice.text() + "' and AccountingDocumentHeaderText eq 'Order " + Record.OrderNumber.text()  + "' and CompanyCode eq '" +  vm.getMappedValue('EBMS', 'OrganizationCode', Record.OrganizationCode.text() , 'S4HC', 'CompanyCode') + "' )";
            
            else refid_query = refid_query +  " or ( DocumentReferenceID eq 'INV " + Record.Invoice.text() + "' and AccountingDocumentHeaderText eq 'Order " + Record.OrderNumber.text()  + "' and CompanyCode eq '" +  vm.getMappedValue('EBMS', 'OrganizationCode', Record.OrganizationCode.text() , 'S4HC', 'CompanyCode' ) + "' )";
        }
      }
  

    message.setProperty('Refid_Query', refid_query);
    return message; 

}



def Message UpdateInvoiceSearchForPI(Message message) {

    def body = message.getBody(java.lang.String) as String; 
  
    def root  = new XmlSlurper().parseText(body);

    root.Record.each{ record -> 
            if( record.Source == 'PI' && record.Line != "1"){
                
           
               record.InvoiceSearch =  record.Organization.text() + "-" + root.Record.find{ it.Organization == record.Organization && it.EntryNumber == record.EntryNumber && it.Line == '1'  }.Invoice.text() + "-" + record.PaymentPlan.text();     
                
            }
                           
            
        } 
    message.setBody(XmlUtil.serialize(root)); 
    return message; 


}



def Message FilterJEDbyGL(Message message) {

    def body = message.getBody(java.lang.String) as String; 
    def vm = ITApiFactory.getApi(ValueMappingApi.class, null);

    def root  = new XmlSlurper().parseText(body);

    root.Record.each{ record -> 
            if( vm.getMappedValue('EBMS', 'GLAccount', record.GLAccount.text() , 'EBMS', 'JEDExclusionFlag') == "X" ){
                
                record.replaceNode{ };   
                
            }
                           
            
        } 
    message.setBody(XmlUtil.serialize(root)); 
    return message; 


}

def Message ChangeRootToLowercase(Message message){
    
    def body = message.getBody(java.lang.String) as String; 
    
    body = body.replaceAll("<Root>", "<root>"); 
    
    body = body.replaceAll("</Root>", "</root>"); 

    
    message.setBody(body); 
    
    return message; 
    
    
    
}





def Message SetPropertyRegOrderQuery(Message message) {

    def body = message.getBody(java.lang.String) as String; 
    def root  = new XmlSlurper().parseText(body);
    def regord_query = "";
    
    root.Item.each { Item -> 
    
        if(regord_query.indexOf( Item.OrderNumber.text()) < 0 ){ 
            if(regord_query != '') regord_query = regord_query + " or ";
            
            regord_query = regord_query + "OrderNumber eq " + Item.OrderNumber.text() + "";
        }
    }
          
    
    message.setProperty('Regord_Query', regord_query);
    return message; 

}




def Message SetRegOrderHeaderValues(Message message) {

    def body = message.getBody(java.lang.String) as String; 
  
    def root  = new XmlSlurper().parseText(body);
    def reghead = new XmlSlurper().parseText(message.getProperty("Regord_Body"));


    root.Item.each { Item -> 
        Item.PONumber = reghead.Record.find{ it.OrderNumber == Item.OrderNumber.text()  }.PONumber.text();
    
    }

    message.setBody(XmlUtil.serialize(root)); 
    return message; 

}


def Message RemoveDuplicatePayments(Message message) {

    def body = message.getBody(java.lang.String) as String;

    body = body.replaceAll("\\<\\?xml(.+?)\\?\\>", "").trim();
    body = body.replaceAll("<multimap:Messages xmlns:multimap=", "").trim();
    body = body.replaceAll("\"http://sap.com/xi/XI/SplitAndMerge\">", "").trim();
    body = body.replaceAll("<multimap:Message1>","").trim();
    body = body.replaceAll("</multimap:Message1>", "" ).trim();
    body = body.replaceAll("</multimap:Messages>", "").trim();
    body = body.replaceAll("<YY1_IF_PAYMENT_DOCUMENTS>", "");
    body = body.replaceAll("</YY1_IF_PAYMENT_DOCUMENTS>", "");
    body = "<YY1_IF_PAYMENT_DOCUMENTS>" + body + "</YY1_IF_PAYMENT_DOCUMENTS>";

    def new_body = "";
    def root  = new XmlSlurper().parseText(body);

    root.YY1_IF_PAYMENT_DOCUMENTSType.each{ Document ->
        
        if( new_body.indexOf(Document.ID.text()) < 0 ) new_body = new_body +  XmlUtil.serialize(Document).replaceAll("\\<\\?xml(.+?)\\?\\>", "").trim();
    
    } 
    
    body = "<YY1_IF_PAYMENT_DOCUMENTS>" + new_body + "</YY1_IF_PAYMENT_DOCUMENTS>";
    body = body.replaceAll("</YY1_IF_PAYMENT_DOCUMENTSType><YY1_IF_PAYMENT_DOCUMENTSType>","</YY1_IF_PAYMENT_DOCUMENTSType>" + "\n" + "<YY1_IF_PAYMENT_DOCUMENTSType>")
    message.setBody(body);
    return message;

}

