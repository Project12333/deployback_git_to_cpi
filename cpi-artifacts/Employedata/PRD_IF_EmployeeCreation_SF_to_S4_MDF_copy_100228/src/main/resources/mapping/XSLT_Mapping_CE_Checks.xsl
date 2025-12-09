<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 <xsl:output omit-xml-declaration="yes" indent="yes"/>
 <xsl:strip-space elements="*"/>

 <xsl:template match="node()|@*">
     <xsl:copy>
       <xsl:apply-templates select="node()|@*"/>
     </xsl:copy>
 </xsl:template>

<!-- Incase of termination of employee; any lastdateworked changes; remove the nodes--> 
<xsl:template match="employment_information/*[not(node())]"/>

<!-- COMPOUND_EMPLOYEE/DELTA_NO_RELEVANT_CHANGE fix V1.0.109 --> 
<xsl:template match="queryCompoundEmployeeResponse/CompoundEmployee[not(person)]"/> 

</xsl:stylesheet>