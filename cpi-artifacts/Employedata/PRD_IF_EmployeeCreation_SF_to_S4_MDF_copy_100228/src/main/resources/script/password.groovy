import com.sap.it.api.mapping.*;

import com.sap.it.api.mapping.MappingContext;

def String getProperty(String password, MappingContext context) {

    def propValue= context.getProperty(password);

    return propValue;

}

