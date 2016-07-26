#!/usr/bin/env python
#########################################################################################
#
# Resample data.
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Julien Cohen-Adad, Sara Dupont
# Modified: 2015-09-08
#
# About the license: see the file LICENSE.TXT
#########################################################################################

# TODO: adjust qform of output data to account for pixel size
# TODO: test if crashes with 2d or 4d data
# TODO: raise exception if input size is not numerical

import sys
# import os
# import getopt
import commands
import sct_utils as sct
# import time
# from sct_convert import convert
from msct_image import Image
from msct_parser import Parser
# import dipy.align.reslice as dp_iso


# DEFAULT PARAMETERS
class Param:
    ## The constructor
    def __init__(self):
        self.debug = 0
        self.fname_data = ''
        self.fname_out = ''
        self.new_size = ''
        self.new_size_type = ''
        self.interpolation = 'linear'
        self.x_to_order = {'nn': 0, 'linear': 1, 'spline': 2}
        self.mode = 'reflect'  # How to fill the points outside the boundaries of the input, possible options: constant, nearest, reflect or wrap
        # constant put the superior edges to 0, wrap does something weird with the superior edges, nearest and reflect are fine
        self.file_suffix = '_resampled'  # output suffix
        self.verbose = 1


# resample
# ======================================================================================================================
def resample():
    """
    Resample data using nipy. Note: we cannot use msct_image because coordmap needs to be used.
    :return:
    """
    import nipy
    from nipy.algorithms.registration import resample
    import numpy as np

    verbose = param.verbose

    # Load data
    sct.printv('\nLoad data...', verbose)
    nii = nipy.load_image(param.fname_data)
    data = nii.get_data()
    # Get dimensions of data
    px, py, pz = nii.header.get_zooms()
    nx, ny, nz = nii.header.get_data_shape()
    sct.printv('  pixdim: '+str(px)+' x '+str(py)+' x '+str(pz)+' mm', verbose)
    sct.printv('  shape: '+str(nx)+' x '+str(ny)+' x '+str(nz)+' vox', verbose)
    # get_base_affine()
    affine = nii.coordmap.affine
    sct.printv('  affine matrix: \n'+str(affine))

    # Calculate new dimensions
    sct.printv('\nCalculate new dimensions...', verbose)
    # parse input argument
    new_size = param.new_size.split('x')
    if param.new_size_type == 'vox':
        nx_r = int(new_size[0])
        ny_r = int(new_size[1])
        nz_r = int(new_size[2])
    elif param.new_size_type == 'factor':
        if len(new_size) == 1:
            # isotropic resampling
            new_size = [new_size[0], new_size[0], new_size[0]]
        nx_r = int(round(nx * float(new_size[0])))
        ny_r = int(round(ny * float(new_size[1])))
        nz_r = int(round(nz * float(new_size[2])))
    else:
        sct.printv('\nERROR: param.new_size_type is not recognized.', 1, 'error')
    sct.printv('  new shape: '+str(nx_r)+' x '+str(ny_r)+' x '+str(nz_r)+' vox', verbose)
    # sct.printv('\nGet dimensions of data...', param.verbose)
    # nx, ny, nz, nt, px, py, pz, pt = input_im.dim
    # sct.printv('  ' + str(px) + ' x ' + str(py) + ' x ' + str(pz)+ ' x ' + str(pt)+'mm', param.verbose)
    # dim = 4  # by default, will be adjusted later
    # if nt == 1:
    #     dim = 3
    # if nz == 1:
    #     dim = 2
    #     sct.run('ERROR (sct_resample): Dimension of input data is different from 3 or 4. Exit program', param.verbose, 'error')

    # create ref image
    arr_r = np.zeros((nx_r, ny_r, nz_r))
    R = np.eye(4)
    R[0, 0] = nx / float(nx_r)
    R[1, 1] = ny / float(ny_r)
    R[2, 2] = nz / float(nz_r)
    affine_r = np.dot(affine, R)
    coordmap_r = nii.coordmap
    coordmap_r.affine = affine_r
    nii_r = nipy.core.api.Image(arr_r, coordmap_r)

    sct.printv('\nCalculate affine transformation...', verbose)
    # create affine transformation
    transfo = R
    # transfo[:3, :3] = np.diag(np.array((0.5, 0.5, 1), dtype='f8'))
    # shift transformation to account for voxel size
    # transfo[:3, 3] = np.array((-0.25, -0.25, -0.25), dtype='f8')
    transfo[:3, 3] = np.array(( (R[0, 0]-1)/2, (R[1, 1]-1)/2, (R[2, 2]-1)/2 ), dtype='f8')
    # print transfo
    sct.printv('  transfo: \n'+str(transfo), verbose)

    # set interpolation method
    if param.interpolation == 'nn':
        interp_order = 0
    elif param.interpolation == 'linear':
        interp_order = 1
    elif param.interpolation == 'spline':
        interp_order = 2

    # resample data
    data_r = resample(nii, transform=transfo, reference=nii_r, mov_voxel_coords=True, ref_voxel_coords=True, dtype=None, interp_order=interp_order)

    if param.fname_out == '':
        fname_out = sct.add_suffix(param.fname_data, '_r')

    # save data
    nii_r = nipy.core.api.Image(data_r, coordmap_r)
    nipy.save_image(nii_r, fname_out)

    # to view results
    sct.printv('\nDone! To view results, type:', verbose)
    sct.printv('fslview '+fname_out+' &', verbose, 'info')

    # new_im = Image(param=new_data)
    # new_im.absolutepath = param.fname_out
    # new_im.path = path_out
    # new_im.file_name = file_out
    # new_im.ext = ext_out

    # zooms_to_set = list(new_zooms)
    # if dim == 4:
    #     zooms_to_set.append(nt)

    # new_im.hdr = input_im.hdr
    # new_im.hdr.set_zooms(zooms_to_set)

    # Set the new sform and qform:
    # new_im.hdr.set_sform(new_affine)
    # new_im.hdr.set_qform(new_affine)
    #
    # new_im.save()

    # extract resampling factor
    # sct.printv('\nParse resampling factor...', param.verbose)
    # new_size_split = param.new_size.split('x')
    # new_size = [float(new_size_split[i]) for i in range(len(new_size_split))]
    # # check if it has three values
    # if not len(new_size) == 3:
    #     sct.printv('\nERROR: new size should have three dimensions. E.g., 2x2x1.\n', 1, 'error')
    # else:
    #     ns_x, ns_y, ns_z = new_size
    #
    # # Extract path/file/extension
    # path_data, file_data, ext_data = sct.extract_fname(param.fname_data)
    # path_out, file_out, ext_out = '', file_data, ext_data
    # else:
    #     file_out += param.file_suffix
    # param.fname_out = path_out+file_out+ext_out
    #
    # input_im = Image(param.fname_data)


    # import numpy as np
    # affine_new = np.array([[2., 0., 0., 1],
    #                 [0., 2., 0., 1],
    #                 [0., 0., 2., 0],
    #                 [0., 0., 0., 1.]])
    # import nibabel
    # img = nibabel.Nifti1Image(input_im.data, affine=affine_new)
    # from nilearn.image import resample_img
    # new_data = resample_img(img, target_affine=np.eye(4), target_shape=(60, 60, 27))
    # print new_data.shape

    # display
    # from matplotlib.pylab import *
    # matshow(data[:, :, 15], cmap=cm.gray), show()
    # matshow(data_r[:, :, 15], cmap=cm.gray), show()

    # # translate before interpolation to account for voxel size
    # from skimage import transform
    # transform.resize()
    #
    #
    # zooms = (px, py, pz)  # input_im.hdr.get_zooms()[:3]
    # affine = input_im.hdr.get_qform()  # get_base_affine()
    # new_zooms = (px_new, py_new, pz_new)
    #
    # if type(param.interpolation) == int:
    #     order = param.interpolation
    # elif type(param.interpolation) == str and param.interpolation in param.x_to_order.keys():
    #     order = param.x_to_order[param.interpolation]
    # else:
    #     order = 1
    #     sct.printv('WARNING: wrong input for the interpolation. Using default value = linear', param.verbose, 'warning')

    import numpy as np
    # affine = np.array([[-2., 0., 0., 29.25],
    #        [0., 2., 0., -29.25],
    #        [0., 0., 2., -31.25],
    #        [0., 0., 0., 1.]])
    # affine = np.array([[-2, 0., 0., 28.25],
    #                    [0., 2., 0., -27.25],
    #                    [0., 0., 2., -31.25],
    #                    [0., 0., 0., 1.]])

    # new_data, new_affine = dp_iso.reslice(input_im.data, affine, zooms, new_zooms, mode=param.mode, order=order)




def get_parser():
    # Initialize the parser
    parser = Parser(__file__)
    parser.usage.set_description('Anisotropic resampling of 3D or 4D data.')
    parser.add_option(name="-i",
                      type_value="file",
                      description="Image to segment. Can be 3D or 4D. (Cannot be 2D)",
                      mandatory=True,
                      example='dwi.nii.gz')
    parser.usage.addSection('TYPE OF THE NEW SIZE INPUT : with a factor of resampling, in mm or in number of voxels\n'
                            'Please choose only one of the 3 options.')
    parser.add_option(name="-f",
                      type_value="str",
                      description="Resampling factor in each dimensions (x,y,z). Separate with \"x\"\n"
                                  "For 2x upsampling, set to 2. For 2x downsampling set to 0.5",
                      mandatory=False,
                      example='0.5x0.5x1')
    # parser.add_option(name="-mm",
    #                   type_value="str",
    #                   description="Resampling size in mm in each dimensions (x,y,z). Separate with \"x\"",
    #                   mandatory=False)
                      # example='0.1x0.1x5')
    parser.add_option(name="-vox",
                      type_value="str",
                      description="Resampling size in number of voxels in each dimensions (x,y,z). Separate with \"x\"",
                      mandatory=False)
                      # example='50x50x20')
    parser.usage.addSection('MISC')
    parser.add_option(name="-x",
                      type_value='multiple_choice',
                      description='Interpolation method.',
                      mandatory=False,
                      default_value='linear',
                      example=['nn', 'linear', 'spline'])

    parser.add_option(name="-o",
                      type_value="file_output",
                      description="Output file name",
                      mandatory=False,
                      example='dwi_resampled.nii.gz')
    parser.add_option(name="-v",
                      type_value='multiple_choice',
                      description="verbose: 0 = nothing, 1 = classic, 2 = expended.",
                      mandatory=False,
                      default_value=1,
                      example=['0', '1', '2'])
    return parser

# ======================================================================================================================
# Start program
# ======================================================================================================================
if __name__ == "__main__":
    # initialize parameters
    param = Param()
    param_debug = Param()

    # Parameters for debug mode
    if param.debug:
        print '\n*** WARNING: DEBUG MODE ON ***\n'
        # get path of the testing data
        status, path_sct_data = commands.getstatusoutput('echo $SCT_TESTING_DATA_DIR')
        param.fname_data = path_sct_data+'/fmri/fmri.nii.gz'
        param.new_size = '2' #'0.5x0.5x1'
        param.remove_tmp_files = 0
        param.verbose = 1
    else:
        parser = get_parser()
        arguments = parser.parse(sys.argv[1:])
        param.fname_data = arguments["-i"]
        arg = 0
        if "-f" in arguments:
            param.new_size = arguments["-f"]
            param.new_size_type = 'factor'
            arg += 1
        # elif "-mm" in arguments:
        #     param.new_size = arguments["-mm"]
        #     param.new_size_type = 'mm'
        #     arg += 1
        elif "-vox" in arguments:
            param.new_size = arguments["-vox"]
            param.new_size_type = 'vox'
            arg += 1
        else:
            sct.printv(parser.usage.generate(error='ERROR: you need to specify one of those three arguments : -f, -mm or -vox'))

        if arg > 1:
            sct.printv(parser.usage.generate(error='ERROR: you need to specify ONLY one of those three arguments : -f, -mm or -vox'))

        if "-o" in arguments:
            param.fname_out = arguments["-o"]
        if "-x" in arguments:
            if len(arguments["-x"]) == 1:
                param.interpolation = int(arguments["-x"])
            else:
                param.interpolation = arguments["-x"]
        if "-v" in arguments:
            param.verbose = int(arguments["-v"])

    # call main function
    resample()
