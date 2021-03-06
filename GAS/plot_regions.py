import os
import textwrap
import warnings
import glob
import numpy as np
from astropy.table import Table, join
from astropy.io import fits
import astropy.units as u
from spectral_cube import SpectralCube
from . import catalogs
from scipy.ndimage import binary_opening
import aplpy

import matplotlib as mpl
mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'

from config import plottingDictionary

def mask_binary(imageHDU,LowestContour,selem):
    map = imageHDU[0].data
    mask = binary_opening(map > LowestContour, selem)
    MaskedMap = mask*map
    imageHDU[0].data = MaskedMap
    return imageHDU, mask

def plot_moments_QA(regions=None,file_extension='all_rebase3',release='all'):

    RegionCatalog = catalogs.GenerateRegions(release=release)
    if regions is None:
        RegionCatalog = catalogs.GenerateRegions(release=release)
    else:
        RegionCatalog = catalogs.GenerateRegions(release=release)
        keep = [idx for idx, row in enumerate(RegionCatalog) if row['Region name'] in regions]
        RegionCatalog = RegionCatalog[keep]

    line_list  = ['NH3_11','NH3_22','NH3_33','C2S','HC5N','HC7N_21_20','HC7N_22_21']
    label_list = ['NH$_3$(1,1)','NH$_3$(2,2)','NH$_3$(3,3)','C$_2$S','HC$_5$N',
                  'HC$_7$N (21-20)','HC$_7$N (22-21)']
    extension = file_extension
    color_table='magma'
    text_color='black'
    text_size = 12
    beam_color='#d95f02'  # previously used '#E31A1C'
    # Try single set of contours for first look images
    w11_step = 0.3
    cont_levs=2**np.arange( 0,20)*(w11_step*1.5)
    w11_lw   = 0.5

    # Masking of small (noisy) regions
    selem = np.array([[0,1,0],[1,1,1],[0,1,0]])

    for ThisRegion in RegionCatalog:
        region = ThisRegion['Region name']
        plot_param = plottingDictionary[region]
        file_w11='{0}/{0}_NH3_11_{1}_mom0_QA_trim.fits'.format(region,extension)
        if os.path.isfile(file_w11):
            LowestContour= cont_levs[0]*0.5
            w11_hdu = fits.open(file_w11)
            map = w11_hdu[0].data
            mask = binary_opening(map > LowestContour, selem)
            MaskedMap = mask*map
            w11_hdu[0].data = MaskedMap
            for i in range(len(line_list)):
                line_i=line_list[i]
                label_i=label_list[i]
                file_mom0='{0}/{0}_{1}_{2}_mom0_QA_trim.fits'.format(region,line_i,extension)
                if os.path.isfile(file_mom0):
                    line_hdu = fits.open(file_mom0)
                    # Use percentiles to set initial plot colourscale ranges
                    v_min=np.nanpercentile(line_hdu[0].data,0.5)
                    v_max=np.nanpercentile(line_hdu[0].data,99.9)
                    fig=aplpy.FITSFigure(file_mom0, hdu=0)
                    if line_i == 'NH3_11':
                        fig.show_colorscale(cmap=color_table,vmin=v_min, vmax=v_max, stretch='log',
                                            vmid=v_min-(1.*np.abs(v_min)))
                        fig.set_nan_color('0.95')
                        cbar_ticks = [0,3,6,12,24,48,96]
                        # add colorbar
                        fig.add_colorbar()
                        fig.colorbar.show(box_orientation='horizontal', width=0.1, pad=0.0, ticks=cbar_ticks,
                                                          location='top', axis_label_text='Integrated Intensity (K km s$^{-1}$)')
                    elif (line_i in ['NH3_22','NH3_33']) :
                        fig.show_colorscale(cmap=color_table,vmin=v_min, vmax=v_max, stretch='linear',
                                            vmid=v_min-(1.*np.abs(v_min)))
                        cbar_ticks = [0,1,2,3,6,12]
                        # add colorbar
                        fig.add_colorbar()
                        fig.colorbar.show(box_orientation='horizontal', width=0.1, pad=0.0, ticks= cbar_ticks,
                                          location='top', axis_label_text='Integrated Intensity (K km s$^{-1}$)')
                    else:
                        fig.show_colorscale( cmap=color_table,vmin=v_min, vmax=v_max)
                        # add colorbar
                        fig.add_colorbar()
                        fig.colorbar.show( box_orientation='horizontal', width=0.1, pad=0.0,
                                          location='top', axis_label_text='Integrated Intensity (K km s$^{-1}$)')
                    fig.colorbar.set_font(family='sans_serif',size=text_size)
                    fig.colorbar.set_axis_label_font(family='sans_serif',size=text_size)
                    #
                    fig.show_contour(w11_hdu, colors='gray', levels=cont_levs, linewidths=w11_lw)
                    # Axis labels
                    fig.axis_labels.set_font(family='sans_serif',size=text_size)
                    # Ticks
                    fig.ticks.set_color(text_color)
                    fig.tick_labels.set_font(family='sans_serif',size=text_size)
                    fig.tick_labels.set_style('colons')
                    fig.tick_labels.set_xformat('hh:mm:ss')
                    fig.tick_labels.set_yformat('dd:mm')
                    # Add beam
                    fig.add_beam(major=0.0088441,minor=0.0088441,angle=0)
                    fig.beam.set_color(beam_color)
                    fig.beam.set_corner('bottom left')
                    # Scale bar
                    # magic line of code to obtain scale in arcsec obtained from
                    # http://www.astropy.org/astropy-tutorials/Quantities.html
                    ang_sep =  (plot_param['scalebar_size'].to(u.au)/plot_param['distance']).to(u.arcsec, equivalencies=u.dimensionless_angles())
                    fig.add_scalebar(ang_sep.to(u.degree))
                    fig.scalebar.set_corner(plot_param['scalebar_pos'])
                    fig.scalebar.set_font(family='sans_serif',size=text_size)
                    fig.scalebar.set(color=text_color)
                    fig.scalebar.set_label('{0:4.2f}'.format(plot_param['scalebar_size']))
                    # Labels
                    label_loc = plot_param['label_loc']
                    label_ha = plot_param['label_ha']
                    fig.add_label(label_loc[0],label_loc[1],
                                  '{0}\n{1}'.format(region,label_i),
                                  relative=True, color=text_color,
                                  horizontalalignment=label_ha,
                                  family='sans_serif',size=text_size)
                    # fig.set_system_latex(True)
                    fig.save( 'figures/{0}_{1}_{2}_mom0_QA_map.pdf'.format(region,line_i,extension),adjust_bbox=True,dpi=200)
                    fig.close()
                else:
                    print('File {0} not found'.format(file_mom0))
        else:
            print('File {0} not found'.format(file_w11))


def plot_rms_QA(regions=None,file_extension='all_rebase3',release='all'):

    RegionCatalog = catalogs.GenerateRegions(release=release)
    if regions is None:
        RegionCatalog = catalogs.GenerateRegions(release=release)
    else:
        RegionCatalog = catalogs.GenerateRegions(release=release)
        keep = [idx for idx, row in enumerate(RegionCatalog) if row['Region name'] in regions]
        RegionCatalog = RegionCatalog[keep]

    line_list  = ['NH3_11','NH3_22','NH3_33','C2S','HC5N','HC7N_21_20','HC7N_22_21']
    label_list = ['NH$_3$(1,1)','NH$_3$(2,2)','NH$_3$(3,3)','C$_2$S','HC$_5$N',
                  'HC$_7$N (21-20)','HC$_7$N (22-21)']
    extension = file_extension
    color_table='magma'
    text_color='black'
    text_size = 12
    beam_color='#d95f02'  # previously used '#E31A1C'

    # Masking of small (noisy) regions
    selem = np.array([[0,1,0],[1,1,1],[0,1,0]])

    for ThisRegion in RegionCatalog:
        region = ThisRegion['Region name']
        plot_param = plottingDictionary[region]
        file_r11='{0}/{0}_NH3_11_{1}_rms_QA_trim.fits'.format(region,extension)
        if os.path.isfile(file_r11):
            for i in range(len(line_list)):
                line_i=line_list[i]
                label_i=label_list[i]
                file_rms='{0}/{0}_{1}_{2}_rms_QA_trim.fits'.format(region,line_i,extension)
                if os.path.isfile(file_rms):
                    line_hdu = fits.open(file_rms)
                    # Use percentiles to set initial plot colourscale ranges
                    v_min=np.nanpercentile(line_hdu[0].data,0.1)
                    v_max=np.nanpercentile(line_hdu[0].data,99.)
                    fig=aplpy.FITSFigure(file_rms, hdu=0)
                    fig.show_colorscale( cmap=color_table,vmin=v_min, vmax=v_max)
                    fig.set_nan_color('0.95')
                    # add colorbar
                    fig.add_colorbar()
                    #fig.colorbar.set_width(0.15)
                    fig.colorbar.show( box_orientation='horizontal', width=0.1, pad=0.0,
                                       location='top', axis_label_text='(K)')
                    fig.colorbar.set_font(family='sans_serif',size=text_size)
                    fig.colorbar.set_axis_label_font(family='sans_serif',size=text_size)
                    # Axis labels
                    fig.axis_labels.set_font(family='sans_serif',size=text_size)
                    # Ticks
                    fig.ticks.set_color(text_color)
                    fig.tick_labels.set_font(family='sans_serif',size=text_size)
                    fig.tick_labels.set_style('colons')
                    fig.tick_labels.set_xformat('hh:mm:ss')
                    fig.tick_labels.set_yformat('dd:mm')
                    # Add beam
                    fig.add_beam(major=0.0088441,minor=0.0088441,angle=0)
                    fig.beam.set_color(beam_color)
                    fig.beam.set_corner('bottom left')
                    # Scale bar
                    # magic line of code to obtain scale in arcsec obtained from
                    # http://www.astropy.org/astropy-tutorials/Quantities.html
                    ang_sep =  (plot_param['scalebar_size'].to(u.au)/plot_param['distance']).to(u.arcsec, equivalencies=u.dimensionless_angles())
                    fig.add_scalebar(ang_sep.to(u.degree))
                    fig.scalebar.set_corner(plot_param['scalebar_pos'])
                    fig.scalebar.set_font(family='sans_serif',size=text_size)
                    fig.scalebar.set(color=text_color)
                    fig.scalebar.set_label('{0:4.2f}'.format(plot_param['scalebar_size']))
                    # Labels
                    label_loc = plot_param['label_loc']
                    label_ha = plot_param['label_ha']
                    fig.add_label(label_loc[0],label_loc[1],
                                  '{0}\n{1}'.format(region,label_i),
                                  relative=True, color=text_color,
                                  horizontalalignment=label_ha,
                                  family='sans_serif',size=text_size)
                    # fig.set_system_latex(True)
                    fig.save( 'figures/{0}_{1}_{2}_rms_QA_map.pdf'.format(region,line_i,extension),adjust_bbox=True)
                    fig.close()
                else:
                    print('File {0} not found'.format(file_rms))
        else:
            print('File {0} not found'.format(file_r11))


def plot_property_maps(regions=None,file_extension='all_rebase3',release='all'):

    RegionCatalog = catalogs.GenerateRegions(release=release)
    if regions is None:
        RegionCatalog = catalogs.GenerateRegions(release=release)
    else:
        RegionCatalog = catalogs.GenerateRegions(release=release)
        keep = [idx for idx, row in enumerate(RegionCatalog) if row['Region name'] in regions]
        RegionCatalog = RegionCatalog[keep]

    ext_list  = [4,3,0,1,2]
    label_list = ['$v_{LSR}$ (km s$^{-1}$)','$\sigma_v$ (km s$^{-1}$)','$T_K$ (K)','$T_{ex}$ (K)','log N(para-NH$_3$)']
    file_list = ['vlsr','sigv','Tk','Tex','N_NH3']
    ctable_list = ['RdYlBu_r','plasma','plasma','hot','plasma'] #'YlGnBu_r'
    text_color='black'
    text_size = 12
    beam_color='#d95f02'  # previously used '#E31A1C'
    # Try single set of contours for first look images
    w11_step = 0.4
    cont_levs=2**np.arange( 0,20)*w11_step
    w11_lw   = 0.5

    # Masking of small (noisy) regions
    selem = np.array([[0,1,0],[1,1,1],[0,1,0]])

    for ThisRegion in RegionCatalog:
        region = ThisRegion['Region name']
        print region
        plot_param = plottingDictionary[region]
        file_w11='{0}/{0}_NH3_11_{1}_mom0_QA_trim.fits'.format(region,file_extension)
        if not os.path.isfile(file_w11):
            file_w11 = '{0}/{0}_NH3_11_{1}_mom0_QA.fits'.format(region,file_extension)
        data_file = '{0}/{0}_parameter_maps_{1}_masked.fits'.format(region,file_extension)
        if os.path.isfile(data_file):
            hdu = fits.open(data_file)
            data = hdu[0].data
            header = hdu[0].header
            hdu.close()
            rm_key=['NAXIS3','CRPIX3','CDELT3', 'CUNIT3', 'CTYPE3', 'CRVAL3']
            # Set header to 2D image for plotting
            for key_i in rm_key:
                header.remove(key_i)
            header['NAXIS'] = 2
            header['WCSAXES'] = 2
            # Get NH3 (1,1) moment contours
            LowestContour= cont_levs[0]*0.5
            w11_hdu = fits.open(file_w11)
            map = w11_hdu[0].data
            mask = binary_opening(map > LowestContour, selem)
            MaskedMap = mask*map
            w11_hdu[0].data = MaskedMap
            for i in range(len(ext_list)):
                propmap = data[ext_list[i]]
                maskedProp = propmap * mask
                maskedProp[maskedProp == 0] = np.nan
                prop_hdu = fits.PrimaryHDU(maskedProp,header)
                label = label_list[i]
                # Use percentiles to set initial plot colourscale ranges without masking
                # Will likely mask later
                # Need different percentiles for vlsr vs. Tk
                if ext_list[i] in [2,3,4]:
                    v_min=np.nanpercentile(maskedProp,2.5)
                    v_max=np.nanpercentile(maskedProp,97.5)
                else:
                    if region == 'OrionA':
                        v_min=5.
                        v_max = 40.
                    else:
                        v_min = np.nanpercentile(maskedProp,5)
                        v_max = np.nanpercentile(maskedProp,95)
                fig=aplpy.FITSFigure(prop_hdu)
                fig.show_colorscale(cmap=ctable_list[i],vmin=v_min, vmax=v_max)
                fig.set_nan_color('0.99')
                # add colorbar
                fig.add_colorbar()
                fig.colorbar.show(box_orientation='horizontal', width=0.1, pad=0.0,# ticks=cbar_ticks,
                                  location='top')#, axis_label_text='Integrated Intensity (K km s$^{-1}$)')
                fig.colorbar.set_font(family='sans_serif',size=text_size)
                fig.colorbar.set_axis_label_font(family='sans_serif',size=text_size)
                #
                fig.show_contour(w11_hdu, colors='gray', levels=cont_levs, linewidths=w11_lw)
                # Axis labels
                fig.axis_labels.set_font(family='sans_serif',size=text_size)
                # Ticks
                fig.ticks.set_color(text_color)
                fig.tick_labels.set_font(family='sans_serif',size=text_size)
                fig.tick_labels.set_style('colons')
                fig.tick_labels.set_xformat('hh:mm:ss')
                fig.tick_labels.set_yformat('dd:mm')
                # Add beam
                fig.add_beam(major=0.0088441,minor=0.0088441,angle=0)
                fig.beam.set_color(beam_color)
                fig.beam.set_corner('bottom left')
                # Scale bar
                # magic line of code to obtain scale in arcsec obtained from
                # http://www.astropy.org/astropy-tutorials/Quantities.html
                ang_sep =  (plot_param['scalebar_size'].to(u.au)/plot_param['distance']).to(u.arcsec, equivalencies=u.dimensionless_angles())
                fig.add_scalebar(ang_sep.to(u.degree))
                fig.scalebar.set_corner(plot_param['scalebar_pos'])
                fig.scalebar.set_font(family='sans_serif',size=text_size)
                fig.scalebar.set(color=text_color)
                fig.scalebar.set_label('{0:4.2f}'.format(plot_param['scalebar_size']))
                # Labels
                label_loc = plot_param['label_loc']
                label_ha = plot_param['label_ha']
                fig.add_label(label_loc[0],label_loc[1],
                              '{0}\n{1}'.format(region,label),
                              relative=True, color=text_color,
                              horizontalalignment=label_ha,
                              family='sans_serif',size=text_size)
                # fig.set_system_latex(True)
                fig.save( 'figures/{0}_{1}_{2}.pdf'.format(region,file_extension,file_list[i]),adjust_bbox=True,dpi=200)
                fig.close()
        else:
            print('File {0} not found'.format(data_file))
