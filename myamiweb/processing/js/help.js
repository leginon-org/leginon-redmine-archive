/**
 * help key : value defined in javascript object notation
 */

var help = {
	'appion' : {
		'runid' : 'Specifies the name associated with the processing results unique to the specified session and parameters.  An attempt to use the same run name for a session using different processing parameters will result in an error.',
		'runname' : 'Specifies the name associated with the processing results unique to the specified session and parameters.  An attempt to use the same run name for a session using different processing parameters will result in an error. The Default is automatically incremented',
		'description' : 'brief description attributed with the processing results',
		'descr' : 'brief description attributed with the processing results',
		'outdir' : 'The base output directory to which files will be stored.  If you are testing, switch \"appion\" to \"temp\".  A subdirectory of the run name will be appended for actual output',
		'checkimages' : 'Choose what images to process here.  Images can be inspected by Viewer or ImageAssessor.  BEST images include ones inspected as KEEP or as EXEMPLAR in the viewer.  NON-REJECTED images include the BEST images above-mentioned and the uninspected ones and therefore exclude only the REJECTED or HIDDEN images.',
		'nowait' : 'After processing all the images collected for this sessiont, this will continue to check if new images have been acquired every 10 minutes.  If after 2 hours, no new images have been acquired, this job will terminate.',
		'background' : 'Minimizes the output when the program runs',
		'imgorder' : 'Change the order in which the images are process, shuffle: process in random order, reverse: process newest images first, normal: process oldest images first',
		'limit' : 'If you do not want to process all the images, enter a number and the program will only process this number of images.  Good for testing a few images before committing the results to the database.',
		'cont' : 'By default you ALWAYS want to continue, unless you are NOT committing to the database yet and you want to reprocess an image.',
		'commit' : 'Stores results to the database.  When testing do NOT commit, but once you are happy with the results start commiting the data, otherwise all information will be lost.',
		'minthresh' : 'Threshold for particle picking from the cross-correlation or dogpicker map.  Any values above this threshold are considered particles.<br/>For template correlation, this should be between 0.0 and 1.0, typically 0.4 to 0.6 is used.<br/>For dogPicker, the value is in terms of standard deviations from the mean divided by four.  Reasonable range from 0.4 to 3.0 with typical values falling between 0.7 and 1.0',
		'maxthresh' : 'Maximum threshold for particle picking from the cross-correlation or dogpicker map.  Any values above this threshold are rejected.<br/>For template correlation, you probably do not need this, but typical values would be between 0.7 and 0.8.<br/>For dogPicker, the values is in terms of standard deviations from the mean divided by four.  Reasonable range from 1.0 to 5.0 with typical values falling between 1.5 and 2.5',
		'maxpeaks' : 'This a feature limits the number of particles allowed in an image.  By default it is set to 1500, but if you want no more than 50 particles an image fill in this value',
		'lpval' : 'Low pass filtering of the image before picking.  This should be about 1/10 to 1/50 of the particle diameter, <I>e.g.</I> for a particle with diameter 150 &Aring;, a low pass of 5-10 &Aring; works pretty good',
		'tiltangle' : 'Tilt Angle of micrographs, exclude all images where tilt angle is not equal to specified value',
		'lpstackval' : 'Low pass filter applied to individual particles',
		'hpstackval' : 'High pass filter applied to individual particles',
		'hpval' : 'High pass filtering of the image before picking.  This removes any darkness gradients in the image.  Typically you could disable this by setting it equal to zero, otherwise 600 work pretty good.  Warning this feature typically normalizes the crud so more particles get picked from crud.',
		'medianval' : 'Median filtering of the image before picking.  This helps remove any noise spikes in the image.  Typical values are 2, 3, or 5.  The bigger the number the more information is thrown away.',
		'binval' : 'Binning of the image.  This takes a power of 2 (1,2,4,8,16) and shrinks the image to help make the processing faster.  Typically you want to use 4 or 8 depending on the quality of the templates.',
		'defocpair' : 'Select this box if you are collecting defocal pairs.  This feature takes both of the en and ef images and aligns them, so you can use makestack later.',
		'maxsize' : 'Max size multiple of the particle peak.  When the peak is found in the thresholded image it has a size in pixels.  If that size is greater than maxsize*particle diameter, then the peak is rejected.',
		'overlapmult' : 'The overlap multiple specifies the minimum distance allowed between two peaks.  If two peaks are closer than overlapmult*particle diameter, then only the larger of the two peaks is retained.',
		'pixlimit' : 'Limit the values of the pixels to within this number of standard deviations from the mean.  0.0 turns this feature off.',
		'kfactor' : 'The k-factor for dogpicker defines the sloppiness in diameter of the picked particles.  A k-factor of 1.00001 gives only the exact diameter (1.0 is not allowed), but a k-factor of 5.0 will pick a wide range of sizes.  Cannot be used with multi-scale dogpicker: numslices or sizerange',
		'numslices' : 'Defines the number of different sizes (or slices) to break up the size range into for separating particles of different size.',
		'sizerange' : 'Defines the range of sizes for separating particles of different size.',
		'invert' : 'If the density of your template is opposite the density of your micrographs, use this flag.  For example, if you are using a template created from negatively-stained data to process ice images, check this box.',
		'nojpegs' : 'Do NOT write out the summary jpegs for image assessor.',
		'edgethresh' : 'The threshold set for edge detection.  ACE searches a range of values to determine a good threshold, but this value should be increased if there are more edges in the power spectrum than in the ring.  Decrease if no edges are detected.',
		'pfact' : 'Location of the upper cutoff frequency.  If thon rings extend beyond the power spectrum cutoff frequency, increase this value.  In cases of low signal to noise ratio with few thon rings, decrease this value.',
		'drange' : 'Use in cases where the signal to noise ratio is so high that the edge detection is incorrect.',
		'resamplefr': 'Sets the sampling size of the CTF.  At high defoci or at higher magnifications, the first thon rings may be so close to the origin that they are not processed by ACE.  In these cases raise the resampling value (2.0 works well in these cases).<br/><br/><TABLE><TR><TD COLSPAN=2>typical values for defocus/apix</TD></TR><TR><TD>0.5</TD><TD>1.2</TD></TR><TR><TD>1.0</TD><TD>1.5</TD></TR><TR><TD>1.5</TD><TD>1.6</TD></TR><TR><TD>2.0</TD><TD>1.8</TD></TR><TR><TD>3.0</TD><TD>2.2</TD></TR><TR><TD>4.0</TD><TD>2.7</TD></TR></TABLE><br/>For example, with defocus = 2.0 (-2.0x10<SUP>-6</SUP> m) and apix (&Aring;/pixel) = 1.63<br/>then defocus/apix = 1.22 and you should use resamplefr=1.6<br/>(as long as its close it should work.)',
		'overlap' : 'During processing, micrographs are cut into a series of smaller images and averaged together to increase the signal to noise ratio.  This value (n) will result in successive images having an overlap of (1-n)*field size.  Increase in cases of very low signal to noise ratio.',
		'field' : 'During processing, micrographs are cut into a series of smaller images and averaged together to increase the signal to noise ratio.  This value refers to the width (in pixels) of the cropped images.',
		'cs' : 'Also referred to as Cs, it corresponds to the imperfection produced by the lenses in the electron microscope.  This is specific to the microscope',
		'pdiam' : 'For template correlator this is used to mask out the particle from the image.  Otherwise, this will be the diameter used by the leginon image viewer for displaying picked particles -	it will NOT affect the size of the boxed particles later on, this is only for display purposes.  ',
		'crudminthresh' : 'Lower limit in gradient amplitude for Canny edge detection.<BR>This should be between 0.0 to 1.0 and should be smaller than that of the high limit',
		'crudmaxthresh' : 'Threshold for Canny edge detector to consider as an edge in the gradient amplitude map.<BR>  The edge is then extended continuously from such places until the gradient falls below the Low threshold<BR>The value should be between 0.0 to 1.0 and should be close to 1.0',
		'blur' : 'Gaussian filter bluring used for producing the gradient amplitude map<BR> 1.0=no bluring',
		'crudstd' : 'Threshold to eliminate false positive regions that picks up the background<BR> The region will be removed from the final result if the intensity standard deviation in the region is below the specified number of standard deviation of the map<BR> Leave it blank or as 0.0 if not considered',
		'convolve' : 'Aggregate finding uses this threshold in determining the cutoff of the particle size convoluted edge map<BR> This value is not applicatable if use other mask types<BR> Leave it blank or as 0.0 if not considered',
		'masktype' : 'Crud: Selexon crudfinder.  Canny edge detector and Convex Hull is used<BR>  Edge: Hole Edge detection using region finder in libCV so that the region can be concave.<BR>  Aggr: Aggregate finding by convoluting Sobel edge with a disk of the particle size.',
		'stackname' : 'name of the output stack, usually start.*',
		'stackdescr' : 'brief description attributed to this stack',
		'stackparticles' : 'Particle selection run providing the coordinates that will be used for extracting the particles',
		'stackinv' : 'Density of your extracted particles will be inverted.  Three dimensional reconstruction packages usually require light density on a dark background.  2-D alignment algorithms usually do not.',
		'stacknorm' : 'normalize each of the particle images',
		'checkimage' : 'This option specifies which images to use for particle extraction.<br /><br /><b><i>Non-rejected: </b></i>images that are specified as "Hidden" in the Leginon Image Viewers or selected to "Reject" using the image assessor will NOT be used for stack creation.  This means that any uninspected images will be processed.<br /><br /><b><i>Best:</i></b> only images that are specified as "Exemplar" in the Leginon Image Viewers or were selected to "Keep" using the image assessor will be used for stack creation.<br /><br /><b><i>All: </i></b>all images will be used, regardless of their status.',
		'boxsize' : 'The size (width & height) of the square area that will be extracted from each raw micrograph, using each particle coordinate as its center.  Generally the box size should be at least 1.5 times greater than the diameter of your particle, an even number, and (if possible) has a small prime factor.<br /> NOTE: This value is in pixels, not Angstroms!',
		'stackbin' : 'Amount to bin the particles by after they are extracted from each image.  Note that this binning occurs AFTER boxing from the raw image, so that your box size must correspond to the UNBINNED micrograph.  Usually bin by 2.',
		'stackdfpair' : 'If you picked your particles on far-from focus images, select this to use the shift information to box out the particles from the close-to focus images',
		'stacklim' : 'Makestack will continue processing micrographs and checking the stack size.  Once the number of particles matches or exceeds this limit, it will stop processing images.  Since all particles from a micrograph are added to the stack before checking, the final stack rarely has exactly the number of particles specified by the limit.  Leave blank to process all the micrographs.',
		'maskrad' : 'Radius of external mask (in Angstroms)',
		'numpart' : 'Number of particles to use',
		'numref' : 'Number of references to use',
		'mirror' : 'Align both regular particles and their mirror image',
		'phaseflip' : 'Check this box if you wish to use the defocus value determined by ACE to flip the phases of the particle images (flipping is performed on each individual particle).  The ACE value with the highest confidence will be used.  Note: Amplitudes are NOT affected.',
		'aceconf' : 'Only micrographs with an ACE confidence equal to or above the value specified will be used in the creation of the stack.  Values range from 0 (lowest confidence) to 1 (greatest confidence).  Empirically a confidence value of 0.8 or greater signifies a good estimation of the defocus.',
		'partcutoff' : 'The automated particle selection functions assign each paticle a correlation value - here you set a range of correlation values to use.  Correlation values that are very high or low may be contamination of noise on the micrograph.',
		'factorlist' : 'These images represent a set of eigenvectors, certain traits of the particles should be presented by each eigenvector.  Choosing an image below will use its eigenvectors as a basis for averaging the particles.',
		'dendrogram' : 'Graphical representation of the clusters produced by the clustering algorithm.',
		'numclass' : 'Particle stack will be aligned according to the selected eigen images and averaged into this number of classes.',
		'apix' : 'Pixel size of the acquired image in Angstroms.  Conversion: (1 nm = 10 Angstroms)',
		'tiltseries': 'Select the tilt series number of the session that corresponds to the tomogram to be uploaded.',
		'session': 'Session name as created at leginon startup on the date of image capture.',
		'extrabin': 'additional binning used to reconstruct the tomogram relative to that of the tilt series images.',
		'tomorunname' : 'Specifies the name associated with the full tomogram processing results unique to the specified tilt series and parameters.  An attempt to use the same run name for a tiltseries using different processing parameters will result in an error.',
		'volume': 'a bounded subvolume (often a specific structure) of the full tomogram.  Leave it blank if uploading full tomogram for boxing later',
		'tomobox': 'a box dimension to define the subvolume in pixels of the tilt series images. x is column, y is row ',
		'mask' : 'Radius of external mask (in pixels)',
		'maxshift' : 'Maximum distance a particle can be translated',
		'excludeClass' : 'Classes from classification that will excluded',
		'commonlineemanprog' : 'EMAN common line program for initial model generation',
		'imask' : 'Inside mask used to exclude inside regions',
		'lp' : 'Lowpass filter radius in Fourier pixels',
		'partnum' : 'Number of particles to use for each view.  This number should be at least 10-20, and at most ~10% of the total particle data set.  50-100 is good for typical data sets of 2000 or more particles.',
		'rounds' : 'Rounds of Euler angle determination to use (2-5)',
		'pdbid' : 'ID for an experimentally determined biological molecule from the RCSB Protein Data Bank (www.rcsb.org)',
		'emdbid' : 'ID for an experimentally determined electron density map from the EM Data Bank',
		'biolunit' : 'Use the functional / oligomeric form of the structure for model creation',
		'eulers' : 'Eulers assigned to the particles for this iteration will be used when creating class averages.',
		'sigma' : 'Standard deviation multiplier to determine the quality of particle to be used.  Setting this to 0, only particles that have a quality factor equal to or greater than the mean quality factor will be used in making the class averages.  A larger sigma will result in fewer particles, but of higher \"quality\".  If no value is specified, all particles will be used.',
		'keepavg' : 'Any particles that have a median euler jump greater than this value will not be used in the class averages',
		'eotest' : 'even and odd class averages will be created in addition to the new class averages, to be used for an even/odd test',
		'angleinc' : 'angular increment for alignment, the smaller the increment the longer it takes to run, default 5, rough run use 10 degrees',
		'fastmode' : 'fast mode is a setting in Xmipp that reduces the time for an iteration after the first round, if off all iterations take a long time, if on then if the the iteration time will drop 90% after the first round, e.g.  60 min after round 1 to 4 min for each iteration after',
		'stack' : 'Input particles to be classified',

/******* IMAGIC terms ********/

		'lpfilt' : 'This should be about 1/10 to 1/50 of the particle diameter, <I>e.g.</I> for a particle with diameter 150 &Aring;, a low pass of 5-10 &Aring; works pretty well.<BR/><BR/> NOTE: Imagic uses filtering values between 0 and 1.  This parameter will be converted in the python script to between 0-1 for use in Imagic.',
		'hpfilt' : 'This removes any darkness gradients in the image.  Typically you could disable this by setting it equal to zero, otherwise 200 works pretty well for IMAGIC.<BR/><BR/> NOTE: Imagic uses filtering values between 0 and 1.  This parameter will be converted in the python script to between 0-1 for use in Imagic.',	
		'mask_radius' :'The mask radius is used during masking / filtering of the stack AND during the creation of eigenimages.  The output images will be normalized inside a circular mask with this radius.  The radius should be chosen such that no part of the molecules are cut off by the resulting mask.  This value may be specified as a fraction of the inner radius of the image or in pixels.  Radius = 1 means that the whole image is used for normalization.',
		'mask_dropoff' : 'If you specify a drop-off the mask will be a soft mask.  The drop-off parameter determines the width of the soft edge (halfwidth of soft-edge Gaussian drop-off) by which the circular mask is smoothed.  A value of 0 specifies a hard mask.',
		'transalign_iter' : 'Translational alignment in imagic has 3 basic steps.  1) A total sum of your images is created, 2) The total sum is rotationally averaged, 3) boxed particles are translationally (X-Y) aligned to the rotationally averaged sum.  In the imagic log file you will be able to see how the translational alignment converges with each iteration.  Generally this happens after ~5 iterations.',
		'box_size' : 'number of columns & number of rows for each particle in the stack (these should be equal)',
		'new_classums' : 'These classums will be created from your input stack so as to maximize the signal-to-noize ratio and IMAGIC\'s ability to assign correct euler angles to your images.  The goal is to represent the different views in your stack with new averages that have an improved SNR.  Choosing 25% of the particles in your stack has worked well in test runs.  For example, if your stack contains 400 particles, input 100 here.',
		'num_classaverages' : 'This value refers to the number of class averages that will be used in creating your initial 3d model (3d0).  It is obtained from the reclassification (SORTED BY MEMBERSHIP), and should be set equal to or slightly less than the the number of reclassified classums.  <BR/><BR/> For example, if you have 100 reclassified classums, and are satisfied with all but the 2 last ones, input 98 here.',
		'choose_projections' : 'This first step is the most crucial part of angular reconstitution.  For asymmetric objects, a minimum of 3 projections is required to determine the relationship between the tilt axes of the projections, and hence their euler angles.  These projections should NOT be related by a tilt around a single rotation axis.  For this reason, it is crucial to examine your class averages and decide which 3 belong to the 3 projection planes (i.e.  X-Y, X-Z, Y-Z).  You can, and probably should, play around with different variations, making sure to check the IMAGIC log file and choose  angles with the largest inter-euler difference and lowest error in angular reconstitution.  <BR/><BR/> Note: Imagic begins all projections with [1] instead of [0]',
		'copy' : 'Duplicate the parameters for this iteration',
		'itn' : 'Iteration Number',
		'shift_orig' : 'Occasionally the motif of certain images can shifted out of the image field during alignment.  In this case we would loose the whole image information so the best thing then is just to do nothing.<BR/><BR/> Give a maximum radial shift beyond which you do not shift the image.  Either you can specify this in pixels directly, or as a fraction of the inner radius of the image.<BR/><BR/> Please note that the maximal shift, which you specify here, is the maximal shift for equivalent rotation/shift, which is the overall shift using the original (usually the pre-treated) images to create the output images.',
		'shift_this' : '		For this refinement you may want to specify a maximum shift, which is allowed to shift the images during this alignment.<BR/><BR/> Please note that this maximal shift is another value than the maximal shift during equivalent rotation/shift, which is the overall shift starting from the original (usually the pre-treated) images.<BR/><BR/>Give a maximum radial shift beyond which you do not shift the image.  Either you can specify this in pixels directly, or as a fraction of the inner radius of the image.',
		'samp_par' : 'To calculate the rotational cross-correlation the input images are transformed into cylindrical co-ordinates.  The horizontal size of these images, and hence the precision of the rotational alignment, depends on sampling parameter, which you have to specify here.  <BR/><BR/>Example: When the sampling parameter is chosen to have the value 4, this means that the number of sampling points along the tangential direction equals four times the radius of the input images.  Reasonable values lie between 4 and 12, with low precision being 4, high precision being 12.',
		'euler_ang_inc' : 'This angular increment is taken as an indication of how precisely you want to determine the euler angles of the input images.  The computing time required for 1 degree is FOUR times more than for 2 degrees, etc.  Can try, for example, 10 in first iterations, and 1-2 in the last iterations.',
		'num_classums' : 'The classums are sorted according to the error in angular reconstitution.  This value is the number of classums that you will use for iterative refinement.  Typically only a handful of classums have a very high error in angular reconstitution, so a good value may be 90-95% of your original classums.  Alternatively, all of them can be used as well.  <BR/><BR/><b> NOTE: ORIGINAL CLASS AVERAGES IN NOREF RUN ARE USED FOR REFINEMENT </b>',
		'ham_win' : '<font size=1.5>A hamming window can be incorporated into the 3d filter to suppress high frequency compontents that cause artefacts such as ringing, streaking, etc.  The effect of a hamming filter is to smooth off the edge of the filter rather than to have a sharp cut-off.  <BR/><BR/>For Hamming Window = 1.  No smooth edge, but rather a sharp cut-off at the nyquist frequency (effectively a circular mask).  <BR/><BR/>For Hamming Window = 0.8, you get a smooth transition from the value "1" at 0.6 times the Nyquist frequency to a value "0" at the Nyquist frequency.  <BR/><BR/>For Hamming Window = 0.5 you get a very smooth transition from the value "1" at the frequency origin, to a value "0" at the Nyquist frequency.  The amplitudes at half the Nyquist frequency will be damped to 0.5 of their original values.  <BR/><BR/>For Hamming Window = 0.2, you get a very smooth transition from the value "1" at the frequency origin, to a value "0" at 0.4 times the Nyquist frequency</size>',
		'obj_size' : 'The relative size of the object inside the 3D volume influences the shape of the exact filter.  A value of "1" means that the reconstructed object entirely fills the reconstruction volume.  A value of ".01" within a volume of 256*256*256 means the 3D object only fills the central 1% of the 3D volume.  If the object is small (relative to the volume size) this means that the width of the central section in Fourier space is relatively large, and that thus intersecting central sections (rather central "slabs") influence each other over a larger frequency range.  <BR/><BR/> Low values (e.g.  0.1) have given poor results in test simulations.  High values (e.g.  0.8) have given better results.  While they may include some noise, this should be eliminated during the automasking procedure.',
		'repalignments' : 'Imagic builds a 3d form your chosen classums.  The batch script is then set up to perform translational and rotational alignments of the reprojections from the built 3d to the classums used to create the 3d.  By iterating this procedure, the 3d-error is minimized.  <BR/><BR/>In test runs alignments have converged after 10-20 iterations.',
		'amask_dim' : 'A good starting point for the lower bound of the bandpass parameter is the smallest dimension of our object.  <BR/><BR/>You can use the formula 2 / (number of pixels for smallest dimension of object).  For example, if it spans 17 pixels, input 0.12 here (2 / 17 = 0.12)',
		'amask_lp' : 'This is a noise-reducing low-pass filter.  Because initial models are done at low resolution, this can be set pretty low (e.g.  0.4)',
		'amask_sharp' : 'The low-pass parameter needs to be >= the low bound of the bandpass.  The higher this filter is set, the "finer / sharper" the mask will be.  Acceptable values from 0-1',
		'amask_thresh' : 'What the program wants from you is what percentage of the voxels (between 0 and 100) you expect the wanted mask to cover.  The program will then automatically generate a threshold value that leads to a 3D mask approximately covering the wanted percentage of the available voxels in the 3D volume.  <BR/><BR/> In test runs, 15 has worked well.',
		'mra_ang_inc' : 'The angular increment for forward projectsions of your masked and filtered 3d used for multi-reference alignment.  You do not need many references here, so setting this paramter to 25 should suffice',
		'forw_ang_inc' : 'The angular increment for forward projections of your masked and filtered 3d used for euler angle refinement (an anchor set).  This value can vary, decreasing as you increase the iterations.  <BR/><BR/>For a C1 structure, choosing 10 should probably be set as the limit, as this creates ~1000 projections which, in combination with an euler angle increment of 2, will take an entire day to perform euler angle assignments for a single iteration',
		'symmetry' : 'imposes symmetry on the model.  Used for multi-reference alignment (MRA), angular reconstitution, threed reconstruction, etc.  e.g.  C1, C2, D7, icosahedral, etc.',
	'numiters' : 'Number of Iterations for multivariate statistical alignment. Typically the eigenimages converge very quickly, within a few iterations, but a large number is set as default to make sure that spikes do not occur later on during convergence.',
	'overcorrection' : 'The overcorrection factor is a very important parameter in the MSA program. It determines the convergence speed of the Eigenvector Eigenvalue algorithm. However, if a too large overcorrection is chosen, the algorithm may start oscillating. Oscillations of the algorithm may be observed in the plot of the sum of the eigenvalues versus iteration number which is part of the output of this program. Divergence may thus only be detected a posteriori. The accepted values for OVER_CORRECTION lie between 0 and 0.9',
	'norefbin' : 'Binning of the image. This takes a power of 2 (1,2,4,8,16) and shrinks the image to help make the processing faster. Binning would be useful if, for example, the reference-free averages are to be used for initial model creation. Otherwise IMAGIC MSA runs are quite fast. For example, on a stack of 10,000 particles with a boxsize of 192, the algorithm takes ~15-30 minutes to run, so bining is not necessary.',


	},

	'eman' : {
/**
* these should be separate
**/
		'imask' : 'Radius of internal mask (in pixels)',
		'nodes' : 'Nodes refers to the number of computer to process on simultaneously.  The more nodes you get the faster things will get process, but more nodes requires that you wait longer before being allowed to begin processing.',
		'walltime' : 'Wall time, also called real-world time or wall-clock time, refers to elapsed time as determined by a chronometer such as a wristwatch or wall clock.  (The reference to a wall clock is how the term originally got its name.)',
		'cputime' : 'Wall time, also called real-world time or wall-clock time, refers to elapsed time as determined by a chronometer such as a wristwatch or wall clock.  (The reference to a wall clock is how the term originally got its name.)',
		'procpernode' : 'Processors per node.  Each computer (node) or Garibaldi has 4 processors (procs), so proc/node=4.  For some cases, you may want to use less processors on each node, leaving more memory and system resources for each process.',
		'ang' : 'Angular step for projections (in degrees)',
		'itn' : 'Iteration Number',
		'copy' : 'Duplicate the parameters for this iteration',
		'mask' : 'Radius of external mask (in pixels)',
		'imask' : 'Radius of internal mask (in pixels)',
		'amask' : '<b>amask=[r],[threshold],[iter]</b><br />Must be used in conjunction with xfiles - This option applies an automatically generated \'form fitting\' soft mask to the model after each iteration.  The mask generation is generally quite good.  It uses 3 values :<br />First - the smallest radius from the center of the map that contacts some density of the \'good\' part of the map.<br />Second - A threshold density at which all of the undesirable density is disconnected from the desired mass.<br />Third - A number of 1-voxel \'shells\' to include after the correct density has been located (this allows you to use threshold densities higher than the desired isosurface threshold density).  The iterative shells will include a \'soft\' Gaussian edge after 2 pixels.  ie - if you add 8 shells, the density will decay in this region using a 1/2 width of 3 pixels starting at the 3rd pixel.  If the number of shells is specified as a negative value, then the mask will have a sharp edge, and any hollow areas inside the mask will be filled in.',
		'sym' : 'Imposes symmetry on the model, omit this option for no/unknown symmetry<BR/>Examples: c1, c2, d7, etc.',
		'hard' : 'Hard limit for <I>make3d</I> program.  This specifies how well the class averages must match the model to be included, 25 is typical',
		'clskeep' : '<b>classkeep=[std dev multiplier]</b><br />This determines how many raw particles are discarded for each class-average.  This is defined in terms of the standard-deviation of the self-similarity of the particle set.  A value close to 0 (should not be exactly 0) will discard about 50% of the data.  1 is a typical value, and will typically discard 10-20% of the data.',
		'clsiter' : 'Generation of class averages is an iterative process.  Rather than just aligning the raw particles to a reference, they are iteratively aligned toeach other to produce a class-average representative of the data, not of the model, eliminating initial model bias.  Typically set to 8 in the early rounds and 3 in later rounds - 0 may be used at the end, but model bias may result.',
		'filt3d' : '<b>fil3d=[rad]</b><br />Applies a gaussian low-pass filter to the 3D model between iterations.  This can be used to correct problems that may result in high resolution terms being upweighted.  [rad] is in pixels, not Angstroms',
		'shrink' : '<b>shrink=[n]</b><br /><i>Experimental</i>, Another option that can produce dramatic speed improvements.  In some cases, this option can actually produce an improvement in classification accuracy.  This option scales the particles and references down by a factor of [n] before classification.  Since data is often heavily oversampled, and classification is dominated by low resolution terms, this can be both safe, and actually improve classification by \'filtering\' out high resolution noise.  Generally shrink=2 is safe and effective especially for early refinement.  In cases of extreme oversampling, larger values may be ok.  This option should NOT be used for the final rounds of refinement at high resolution.',
		'euler2' : '<b>euler2=[oversample factor]</b><br /><i>Experimental</i>, This option should improve convergence and reconstruction quality, but has produced mixed results in the past.  It adds an additional step to the refinement process in which class-averages orientations are redetermined by projection-matching.  The parameter allows you to decrease the angular step (ang=) used to generateprojections.  ie - 2 would produce projections with angular step of ang/2.  It may be worth trying, but use it with caution on new projects.',
		'perturb' : '<i>Experimental</i>, potentially useful and at worst should be harmless.  Has not been well characterized yet.  Rather than generating Euler angles at evenly spaced positions, it adds some randomness to the positions.  This should produce a more uniform distribution of data in 3D Fourier space and reduce Fourier artifacts',
		'xfiles' : '<b>xfiles=[mass in kD]</b><br />A convenience option.  For each 3D model it will produce a corresponding x-file (threed.1a.mrc -> x.1.mrc).  Based on the mass, the x-file will be scaled so an isosurface threshold of 1 will contain the specified mass.',
		'tree' : 'This can be a risky option, but it can produce dramatic speedups in the refinement process.  Rather than comparing each particle to every reference, this will decimate the reference population to 1/4 (if 2 is specified) or 1/9 (if 3 is specified) of its original size, classify, then locally determine which of the matches is best.  Is is safest in conjunction with very small angular steps, ie - large numbers of projections.  The safest way to use this is either:<br /><i>a)</i> for high-resolution, small-ang refinement or <br/><i>b)</i> for the initial iterations of refinement (then turn it off for the last couple of iterations).',
		'median' : 'When creating class averages, use the median value for each pixel instead of the average.  Not recommended for larger datasets, as it can result in artifacts.  If your dataset is noisy, and has small particles this is recommended',
		'phscls' : 'This option will use signal to noise ratio weighted phase residual as a classification criteria (instead of the default optimized real space variance).  Over the last year or so, people working on cylindrical structures (like GroEL), have noticed that \'side views\' of this particle seem to frequently get classified as being tilted 4 or 5 degrees from the side view.  While apparently this didn\'t effect the models significantly at the obtained resolution, it is quite irritating.  This problem turns out to be due to resolution mismatch between the 3D model and the individual particles.  Using phase residual solves this problem, although it\'s unclear if there is any resolution improvement.  This option has a slight speed penalty',
		'fscls' : 'An improvement, albeit an experimental one, over phasecls.  phasecls ignores Fourier amplitude when making image comparisons.  fscls will use a SNR weighted Fourier shell correlation as a similarity criteria.  Preliminary tests have shown that this produces slightly better results than phasecls, but it should still be used with caution.',
		'refine' : 'This will do subpixel alignment of the particle translations for classification and averaging.  May have a significant impact at higher resolutions (with a speed penalty).',
		'goodbad' : 'Saves good and bad class averages from 3D reconstruction.  Overwrites each new iteration.',
		'eotest' : 'Run the <I>eotest</I> program that performs a 2 way even-odd test to determine the resolution of a reconstruction.',
		'coran' : 'Use correspondence analysis particle clustering algorithm',
	},
	
	'frealign' : {
		'copy' : 'Duplicate the parameters for this iteration',	
		'itn' : 'Iteration Number',
		
		/* paste results from runFrealign.convertParserToJSHelp here */	 
		'format' : 'MRC',
		'mode' : 'Run mode.  0: use input parameters and reconstruct with no refinement.  1: refine and reconstruct.  2: randomise particle params and reconstruct.  3: systematic param search and refinement 4: fancy systematic param search and refinement.',
		'magrefine' : 'Magnification refinement',
		'defocusrefine' : 'Defocus refinement',
		'astigrefine' : 'Astigmatism refinemet',
		'fliptilt' : 'Rotation of theta by 180 degrees',
		'ewald' : 'Ewald curvature correction.  0: no correction.  1: correction by insertion method.  2: correction by ref-based method',
		'matches' : 'Write out particles with matching projections',
		'history' : 'Write out history of itmax randomization trials',
		'finalsym' : 'Apply final real space symmetrization to beautify reconstruction',
		'fomfilter' : 'Apply FOM filter to final reconstruction',
		'fsc' : 'Internally calculate FSC between even and odd particles',
		'radius' : 'Radius from center of particle to outer edge',
		'iradius' : 'Inner mask radius',
		'apix' : 'Pixel size in angstroms',
		'ampcontrast' : 'Amplitude contrast',
		'maskthresh' : 'Standard deviations above mean for masking of input model.  0.0 gives no masking.',
		'phaseconstant' : 'Conversion constant for phase residual weighting of particles.  100 gives equal weighting',
		'avgresidual' : 'Average phase residual of all particles.  Used for weighting',
		'ang' : 'Step size if using modes 3 and 4',
		'itmax' : 'Number of iterations of randomization.  Used for modes 2 and 4',
		'maxmatch' : 'Number of potential matches in a search that should be tested further in local refinement',
		'psi' : 'Refine psi',
		'theta' : 'Refine theta',
		'phi' : 'Refine phi',
		'deltax' : 'Refine delta X',
		'deltay' : 'Refine delta Y',
		'first' : 'First particle',
		'last' : 'Last particle',
		'sym' : 'Symmetry.  Cn, Dn, T, O, I, I1, I2',
		'relmag' : 'Relative magnification of dataset?',
		'targetresidual' : 'Target phase residual during refinement',
		'residualthresh' : 'Phase residual threshold cut-off.  Particles with residuals above threshold are not included in the reconstruction',
		'cs' : 'Spherical aberation',
		'kv' : 'Accelerlating voltage',
		'beamtiltx' : 'Beam tilt x (mrad)',
		'beamtilty' : 'Beam tilt y (mrad)',
		'reslimit' : 'Resolution to which to limit the reconstruction',
		'hp' : 'Upper limit for low resolution signal',
		'lp' : 'Lower limit for high resolution signal',
		'bfactor' : 'Bfactor to apply to particles before classification.  0.0 applies no bfactor.',
		'stack' : 'Input particles to be classified',
		'matchstack' : 'Output projection matches',
		'inpar' : 'Input particle parameter file',
		'outpar' : 'Output particle parameter file',
		'outshiftpar' : 'Output particle shift parameter file',
		'invol' : 'Input reference volume',
		'weight3d' : '???',
		'oddvol' : 'Output odd volume',
		'evenvol' : 'Output even volume',
		'outresidual' : '3d phase residuals',
		'pointspreadvol' : 'Output 3d point spread function',
		'stackid' : 'Stack id from database',
		'mrchack' : 'Hack to fix machine stamp in mrc header',
		'outvol' : 'Name of output volume',
		'proc' : 'Number of processors',
		'setuponly' : 'If setuponly is specified, everything will be set up but frealign will not be run',
	}	
}
