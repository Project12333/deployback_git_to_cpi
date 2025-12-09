import com.sap.it.api.ITApi
import com.sap.it.api.ITApiFactory
import com.sap.it.api.securestore.*;
import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message processData(Message message) {
    //Body 
       def body = message.getBody();
       String password;
       String _output="";
       def service = ITApiFactory.getApi(SecureStoreService.class, null);
       def map = message.getProperties();
       def value = map.get("refresh_token");
       
        def value1 = map.get("Refresh Token(Auto)");      // refresh token manually updated
          if ( value1 != 'Auto' )
            {
                 value = value1;
            } 

              //Name of secure parameter
       def credential = service.getUserCredential("OpenAirRefreshTokenBody"); 
        if (credential == null)
        { throw new IllegalStateException("No credential found for alias 'OpenAirRefreshTokenBody'");             
        }
        else{
            password= new String(credential.getPassword());
            }

        //store it in property which can be used in later stage of your integration process.
        message.setBody(password + value);
       return message;
}