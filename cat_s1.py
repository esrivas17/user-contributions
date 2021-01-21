#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Script to combine frames from Sentinel-1 that are slightly offset from each other into a single consistent frame
Input data are SAFE files and a pair of (lon,lat) points

Created on Mon Oct 23 10:43:44 2017

@author: elindsey
"""

import os, s1_func, gmtsar_func, argparse, string, random, multiprocessing, shutil

######################## Command-line execution ########################

if __name__ == '__main__':

    # required arguments: a directory or set of directories to search, orbit directories, latitude bounds, and A/D to specify the orbit direction
    parser = argparse.ArgumentParser(description='Combine bursts from several Sentinel-1 scenes into a single frame, given a min/max lat. bound')
    parser.add_argument('searchdirs',type=str,nargs='+',help='List of directories (or wildcards) containing SAFE or .zip files to be combined.')
    parser.add_argument('-o','--orbit',type=str,action='append',required=True,help='Path to a directory holding orbit files, required. Repeat option to search multiple directories.')
    parser.add_argument('-l','--lonlat',type=str,required=True,help='Lon/Lat pins for the crop script in the GMT R-argument format lon1/lat1/lon2/lat2, required.')
    parser.add_argument('-d','--direction',type=str,required=True,help='Orbit direction (A/D), required.')
    # optional arguments
    parser.add_argument('-n','--nproc',type=int,default=1,help='Number of processors to run in parallel, optional (default: 1)')
    parser.add_argument('-z','--unzipped',action='store_true',default=False,help='Use unzipped SAFE directories instead of the original zip files (default: true).')
    # parse
    args = parser.parse_args()

    # read lons/lats into arrays
    lonlats=[float(i) for i in args.lonlat.split('/')]
    lons=lonlats[0::2]
    lats=lonlats[1::2]

    # create a file for gmtsar to read. This requires the user to input 'A' or 'D' as args.direction
    ll_fname = 'two_pins.ll'
    s1_func.write_ll_pins(ll_fname, lons, lats, args.direction)

    # find a list of all scenes and organize them by orbit number.
    if args.unzipped:
        ftype='SAFE'
    else:
        ftype='zip'
    [images_by_orbit, eofs] = s1_func.find_images_by_orbit(args.searchdirs, args.orbit, ftype)
    print('found %d orbits'%len(images_by_orbit))
    
    argslist=[]
    # for each satellite pass
    for ab_orbit in images_by_orbit:
        print('working on orbit %s'%ab_orbit)
        print('images: %s'%images_by_orbit[ab_orbit])
        print('EOF: %s\n'%eofs[ab_orbit])

        log_fname='log_%s.txt'%ab_orbit
        safe_fname = 'SAFE_filelist_%s.txt'%ab_orbit
        temp_workdir = 'temp_cat_orbit_' + ab_orbit

        # append args to list of tuples for parallel run
        argslist.append( (images_by_orbit[ab_orbit], eofs[ab_orbit], ll_fname, log_fname, temp_workdir, args.unzipped) )

    # run GMTSAR function 'create_frame_tops.csh' in parallel
    with multiprocessing.Pool(processes=args.nproc) as pool:
        pool.starmap(s1_func.create_frame_tops_parallel, argslist)
        
