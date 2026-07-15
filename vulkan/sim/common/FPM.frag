void fpm_frag_main() 
{
	
	// Get triangle number and if its index is zero return.
	uint index		= gl_PrimitiveID;
	if (index == 0)
	{	
		discard;
	}
	//outColor = vec4(1.0,0.0,0.0,1.0);
	outColor = fragColor,1.0;
		
}
