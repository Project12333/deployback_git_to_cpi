import com.sap.it.api.mapping.*;

import com.sap.it.api.mapping.MappingContext;

def String getProperty(String username, MappingContext context) {

    def propValue= context.getProperty(username);

    return propValue;

}

