<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" >
    <xsl:output method="xml" encoding="UTF-8" indent="yes" />
<xsl:strip-space elements="*"/>
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

<!-- Incase of full mode execution; only active employees required in payload -->
<!-- Hence remove the all inactive employee's -->
<xsl:template match="//request/CreateUser/User[cust_Inactivated_In_Prism__c ='1']"/>

</xsl:transform>


<!--
<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" >
<xsl:output method="xml" encoding="UTF-8" indent="yes" />


	<xsl:template match="@* | node()">
		<xsl:copy>
			<xsl:apply-templates select="@* | node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="//CompoundEmployee/person/employment_information/job_information">
		<xsl:copy>
			<xsl:apply-templates select="node() except job_information"/>
			<xsl:for-each select="job_information">
				<xsl:sort select="start_date" data-type="text" order="descending"/>
				<xsl:if test="position()=1">
					<xsl:copy-of select="."/>
				</xsl:if>
			</xsl:for-each>
		</xsl:copy>
	</xsl:template> 

	<xsl:template match="//CompoundEmployee/person/employment_information/job_relation">
		<xsl:copy>
			<xsl:apply-templates select="node() except job_relation"/>
			<xsl:for-each select="job_relation">
				<xsl:sort select="start_date" data-type="text" order="descending"/>
				<xsl:if test="position()=1">
					<xsl:copy-of select="."/>
				</xsl:if>
			</xsl:for-each>
		</xsl:copy>
	</xsl:template> 
-->



<!--

<xsl:strip-space elements="*"/>
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template> 

-->

<!-- Incase of full mode execution; only active Russian employees required in payload -->
<!-- Hence remove the all Terminated/Retired employee's 
<xsl:template match="//root/row[emplStatus ='T']"/>
<xsl:template match="//root/row[emplStatus ='R']"/>
-->
<!--
<xsl:template match="//queryCompoundEmployeeResponse/CompoundEmployee/person/employment_information/job_information[emplStatus ='T']"/>
<xsl:template match="//queryCompoundEmployeeResponse/CompoundEmployee/person/employment_information/job_information[emplStatus ='R']"/>



</xsl:transform>-->