"""
SCons.Tool.cuda

CUDA Tool for SCons

Example:


import os

env = Environment()
env.Tool('cuda')
obj = env.Object('source_device.cu', NVCCFLAGS=['-Xptxas', '-v'], LIBS=['cuda', 'cudart'])
env.Program(['source.cpp', obj], LIBS=['cuda', 'cudart'])

# Generate PTX file.
ptx = env.Ptx('source_device.cu')

"""

import os
import sys
from SCons.Builder import Builder
import SCons.Tool
import SCons.Scanner.C
import SCons.Defaults

CUDAScanner = SCons.Scanner.C.CScanner()

# this object emitters add '.linkinfo' suffixed files as extra targets
# these files are generated by nvcc. The reason to do this is to remove
# the extra .linkinfo files when calling scons -c
def CUDANVCCStaticObjectEmitter(target, source, env):
        tgt, src = SCons.Defaults.StaticObjectEmitter(target, source, env)
#        for file in src:
#                lifile = os.path.splitext(src[0].rstr())[0] + '.linkinfo'
#                tgt.append(lifile)
        return tgt, src
def CUDANVCCSharedObjectEmitter(target, source, env):
        tgt, src = SCons.Defaults.SharedObjectEmitter(target, source, env)
#        for file in src:
#                lifile = os.path.splitext(src[0].rstr())[0] + '.linkinfo'
#                tgt.append(lifile)
        return tgt, src

def generate(env):
        staticObjBuilder, sharedObjBuilder = SCons.Tool.createObjBuilders(env);
        staticObjBuilder.add_action('.cu', '$STATICNVCCCMD')
        staticObjBuilder.add_emitter('.cu', CUDANVCCStaticObjectEmitter)
        sharedObjBuilder.add_action('.cu', '$SHAREDNVCCCMD')
        sharedObjBuilder.add_emitter('.cu', CUDANVCCSharedObjectEmitter)
        SCons.Tool.SourceFileScanner.add_scanner('.cu', CUDAScanner)

        # default compiler
        env['NVCC'] = 'nvcc'

        # default flags for the NVCC compiler
        env['NVCCFLAGS'] = '-I$CUDA_SDK_PATH/C/common/inc'
        env['STATICNVCCFLAGS'] = ''
        env['SHAREDNVCCFLAGS'] = ''
        env['ENABLESHAREDNVCCFLAG'] = '-shared'

        # default NVCC commands
        env['STATICNVCCCMD'] = '$NVCC -o $TARGET -c $NVCCFLAGS $STATICNVCCFLAGS $SOURCES'
        env['SHAREDNVCCCMD'] = '$NVCC -o $TARGET -c $NVCCFLAGS $SHAREDNVCCFLAGS $ENABLESHAREDNVCCFLAG $SOURCES'

        # helpers
        home=os.environ.get('HOME', '')
        programfiles=os.environ.get('PROGRAMFILES', '')
        homedrive=os.environ.get('HOMEDRIVE', '')

        # find CUDA Toolkit path and set CUDA_TOOLKIT_PATH
        cudaToolkitPath = None
        try:
                cudaToolkitPath = env['CUDA_TOOLKIT_PATH']
        except:
                paths=[ home + '/NVIDIA_CUDA_TOOLKIT',
                        home + '/Apps/NVIDIA_CUDA_TOOLKIT',
                           home + '/Apps/NVIDIA_CUDA_TOOLKIT',
                           home + '/Apps/CudaToolkit',
                           home + '/Apps/CudaTK',
                           '/usr/lib/nvidia-cuda-toolkit',
                           '/usr/local/NVIDIA_CUDA_TOOLKIT',
                           '/usr/local/CUDA_TOOLKIT',
                           '/usr/local/cuda_toolkit',
                           '/usr/local/CUDA',
                           '/usr/local/cuda',
                           '/Developer/NVIDIA CUDA TOOLKIT',
                           '/Developer/CUDA TOOLKIT',
                           '/Developer/CUDA',
                           programfiles + 'NVIDIA Corporation/NVIDIA CUDA TOOLKIT',
                           programfiles + 'NVIDIA Corporation/NVIDIA CUDA',
                           programfiles + 'NVIDIA Corporation/CUDA TOOLKIT',
                           programfiles + 'NVIDIA Corporation/CUDA',
                           programfiles + 'NVIDIA/NVIDIA CUDA TOOLKIT',
                           programfiles + 'NVIDIA/NVIDIA CUDA',
                           programfiles + 'NVIDIA/CUDA TOOLKIT',
                           programfiles + 'NVIDIA/CUDA',
                           programfiles + 'CUDA TOOLKIT',
                           programfiles + 'CUDA',
                           homedrive + '/CUDA TOOLKIT',
                           homedrive + '/CUDA',
                           '/usr/bin', ]
                for path in paths:
                        if os.path.isdir(path):
                                print 'scons: CUDA Toolkit found in ' + path
                                cudaToolkitPath = path
                                break
                if cudaToolkitPath == None:
                        sys.exit("Cannot find the CUDA Toolkit path. Please modify your SConscript or add the path in cudaenv.py")
        env['CUDA_TOOLKIT_PATH'] = cudaToolkitPath

        # find CUDA SDK path and set CUDA_SDK_PATH
        cudaSDKPath = None
        try:
                cudaSDKPath = env['CUDA_SDK_PATH']
        except:
                paths=[ home + '/NVIDIA_GPU_Computing_SDK',
                        home + '/local/opt/NVIDIA_GPU_Computing_SDK',
                        home + '/Apps/NVIDIA_GPU_Computing_SDK',
                        home + '/NVIDIA_CUDA_SDK', # i am just guessing here
                        home + '/Apps/NVIDIA_CUDA_SDK',
                           home + '/Apps/CudaSDK',
                           '/usr/local/NVIDIA_CUDA_SDK',
                           '/usr/local/CUDASDK',
                           '/usr/local/cuda_sdk',
                           '/Developer/NVIDIA CUDA SDK',
                           '/Developer/CUDA SDK',
                           '/Developer/CUDA',
                           programfiles + 'NVIDIA Corporation/NVIDIA CUDA SDK',
                           programfiles + 'NVIDIA/NVIDIA CUDA SDK',
                           programfiles + 'NVIDIA CUDA SDK',
                           programfiles + 'CudaSDK',
                           homedrive + '/NVIDIA CUDA SDK',
                           homedrive + '/CUDA SDK',
                           homedrive + '/CUDA/SDK']
                for path in paths:
                        if os.path.isdir(path):
                                print 'scons: CUDA SDK found in ' + path
                                cudaSDKPath = path
                                break
                if cudaSDKPath == None:
                        #sys.exit("Cannot find the CUDA SDK path. Please set env['CUDA_SDK_PATH'] to point to your SDK path")
                        print "Cannot find the CUDA SDK path. Please set env['CUDA_SDK_PATH'] to point to your SDK path"
                        env['NO_CUDA'] = True
                        return
        env['CUDA_SDK_PATH'] = cudaSDKPath

        # cuda libraries
        if env['PLATFORM'] == 'posix':
                cudaSDKSubLibDir = '/linux'
        elif env['PLATFORM'] == 'darwin':
                cudaSDKSubLibDir = '/darwin'
        else:
                cudaSDKSubLibDir = ''

        # add nvcc to PATH
        env.PrependENVPath('PATH', cudaToolkitPath + '/bin')

        # add required libraries
        CPPPATH=[cudaSDKPath + '/shared/inc', 
                    cudaSDKPath + '/C/common/inc', 
                    cudaSDKPath + '/common/inc', 
                    cudaToolkitPath + '/include']
        env.Append(CPPPATH=CPPPATH)
        LIBPATH=[cudaSDKPath + '/lib', 
                    cudaSDKPath + '/C/lib', 
                    cudaSDKPath + '/shared/lib', 
                    cudaSDKPath + '/common/lib' + cudaSDKSubLibDir, 
                    cudaSDKPath + '/C/common/lib' + cudaSDKSubLibDir, 
                    cudaToolkitPath + '/lib64',
                    cudaToolkitPath + '/lib']
        env.Append(LIBPATH=LIBPATH)
        env.Append(LIBS=['cudart'])

        DECUDA_PATH = 'site_scons/site_tools/cuda/decuda'

        ptx_bld = Builder(action = '$NVCC -o $TARGET $NVCCFLAGS -ptx $SOURCE', suffix='.ptx')
        env.Append(BUILDERS = {'Ptx' : ptx_bld})
        elf_bld = Builder(action = '$NVCC -o $TARGET $NVCCFLAGS -cubin $SOURCE', suffix='.elf')
        env.Append(BUILDERS = {'Elf' : elf_bld})
        cubin_bld = Builder(action = DECUDA_PATH + '/elfToCubin.py $SOURCE > $TARGET', suffix='.cubin')
        env.Append(BUILDERS = {'Cubin' : cubin_bld})
        txt_bld = Builder(action = DECUDA_PATH + '/decuda.py -o $TARGET $SOURCE', suffix='.txt')
        env.Append(BUILDERS = {'DeCubin' : txt_bld})


def exists(env):
        return env.Detect('nvcc')
