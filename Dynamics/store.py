

class Store():
    
    def __init__(self):
        pass

     ##################################################################
    #
    # Save storge values
    #
    ##################################################################
    def save_data(self,data_file_name,pary):
        for src in pary:
            for cc in src.collision_list:
                file_name = data_file_name+f"{src.pnum}C{cc.stor_col_num[0]}.csv"
                try:
                    with open(file_name, 'w', newline='') as csvfile:
                        csvfile.write("P,t,iter,vx,vy,pen_factor,v_mag,vel_mag_in,v_coll,v_ang,ang_acc,ang_diff,imomx,imomy,imom,tot_area,cur_area,area_diff,vx_rel,vy_rel,v_rel,col_acc_x,col_acc_y,col_acc_mag,p_mom_x,p_mom_y,p_mom\r\n")
                        for ii in range(len(src.stor_t)):
                            line = f"{src.stor_pnum[ii]},{src.stor_t[ii]:0.4f},{src.stor_iter[ii]},{src.stor_vx[ii]:0.4f},{src.stor_vy[ii]:0.4f},"
                            line += f"{cc.stor_pen_factor[ii]:0.8f},{src.stor_v_mag[ii]:0.8f},"
                            line += f"{src.stor_vel_mag_in[ii]:0.8f},{cc.stor_v_coll[ii]:0.4f},"
                            line += f"{src.stor_v_ang[ii]:0.4f},{cc.stor_vel_ang_acc[ii]:0.8f},{cc.stor_vel_ang_diff[ii]:0.8f},"
                            line += f"{cc.stor_internal_momx[ii]:0.4f},{cc.stor_internal_momy[ii]:0.4f},{src.stor_internal_mom[ii]:0.8f},"
                            line += f"{cc.stor_tot_area[ii]:0.8f},{cc.stor_cur_area[ii]:0.8f},{cc.stor_area_diff[ii]:0.8f},"
                            line += f"{cc.stor_vx_rel[ii]:0.8f},{cc.stor_vy_rel[ii]:0.8f},{cc.stor_v_rel[ii]:0.8f},"
                            line += f"{cc.stor_tot_collision_x_acc[ii]:0.8f},{cc.stor_tot_collision_y_acc[ii]:0.8f},{cc.stor_tot_collision_acc[ii]:0.8f},"
                            line += f"{cc.stor_pred_mom_xout[ii]:0.8f},{cc.stor_pred_mom_yout[ii]:0.8f},{cc.stor_pred_mom_mag[ii]:0.8f}\r\n"
                            csvfile.write(line)
                except BaseException as e:
                    print(f"save_data() error: {e}")
                print(f"Saved particle {src.pnum} Collision {cc.stor_col_num[0]}")    
            
    ##################################################################
    #
    # Clear storage variables
    #
    ##################################################################
    def clear_storage_variables(self,src):
        self.iteration = 0
        self.current_time = 0.0
        src.stor_t.clear()
        src.stor_iter.clear()
        src.stor_vx.clear()
        src.stor_vy.clear()

        src.stor_v_mag.clear()
        src.stor_v_ang.clear()
        src.stor_vel_mag_in.clear()
        src.stor_pnum.clear()
        for cc in src.collision_list:
            cc.stor_tot_area.clear()
            cc.stor_v_coll.clear()
            cc.stor_col_num.clear()
            cc.stor_area_diff.clear()
            cc.stor_internal_mom.clear()
            cc.stor_pen_factor.clear()
            cc.stor_tot_collision_x_acc.clear()
            cc.stor_tot_collision_y_acc.clear()
            cc.stor_tot_collision_acc.clear()
            cc.stor_cur_area.clear()
            cc.stor_pred_mom_xout.clear()
            cc.stor_pred_mom_yout.clear()
            cc.stor_internal_momx.clear()
            cc.stor_internal_momy.clear()
            cc.stor_v_rel.clear()
            cc.stor_vx_rel.clear()
            cc.stor_vy_rel.clear()
            cc.stor_vel_ang_diff.clear()
            cc.stor_vel_ang_acc.clear()

            #src.stor_pen_factor.clear()
    
    ##################################################################
    #
    # Stor storge values
    #
    ##################################################################
    def set_storage_variables(self,src,ct,it):
        
        # Store 
        src.stor_t.append(ct) 
        src.stor_iter.append(it)
        src.stor_vx.append(src.vx)
        src.stor_vy.append(src.vy)
        src.stor_internal_mom.append(src.internal_mom)
        src.stor_v_mag.append(src.vel_mag)
        src.stor_v_ang.append(src.vel_ang)
        src.stor_vel_mag_in.append(src.vel_mag_in)
        src.stor_pnum.append(src.pnum)
        
        
        for cc in src.collision_list:
            if cc.col_flag == True:
                cc.stor_col_num.append(cc.col_num)
                cc.stor_v_coll.append(cc.v_coll_sum)
                cc.stor_area_diff.append(cc.area_diff)
                #cc.stor_internal_mom.append(cc.internal_mom)
                cc.stor_pen_factor.append(cc.pen_factor)
                cc.stor_tot_collision_x_acc.append(cc.tot_collision_x_acc)
                cc.stor_tot_collision_y_acc.append(cc.tot_collision_y_acc)
                cc.stor_tot_collision_acc.append(cc.tot_collision_acc)
                cc.stor_cur_area.append(cc.cur_area)  
                cc.stor_tot_area.append(cc.tot_area)  
                cc.stor_pred_mom_xout.append(cc.pred_mom_xout)
                cc.stor_pred_mom_yout.append(cc.pred_mom_yout)
                cc.stor_pred_mom_mag.append(cc.pred_mom_mag)
                cc.stor_internal_momx.append(cc.internal_momx)
                cc.stor_internal_momy.append(cc.internal_momy)
                cc.stor_v_rel.append(cc.v_rel)
                cc.stor_vx_rel.append(cc.vx_rel)
                cc.stor_vy_rel.append(cc.vy_rel)
                cc.stor_vel_ang_acc.append(cc.vel_ang_acc)
                cc.stor_vel_ang_diff.append(cc.vel_ang_diff)
                #cc.stor_prev_vel_ang.append(cc.prev_vel_ang)
            else:
                if len(cc.stor_tot_area) > 1:
                    cc.stor_tot_area.append(cc.stor_tot_area[-1])  
                else:
                    cc.stor_tot_area.append(0.0)  
                cc.stor_col_num.append(0.0)
                cc.stor_v_coll.append(0.0)
                if len(cc.stor_tot_area) > 1:
                    cc.stor_area_diff.append(cc.stor_area_diff[-1])
                else:
                    cc.stor_area_diff.append(0.0)
                #cc.stor_internal_mom.append(cc.internal_mom)
                cc.stor_pen_factor.append(0.0)
                cc.stor_tot_collision_x_acc.append(0.0)
                cc.stor_tot_collision_y_acc.append(0.0)
                cc.stor_tot_collision_acc.append(0.0)
                cc.stor_cur_area.append(0.0)  
                cc.stor_pred_mom_xout.append(0.0)
                cc.stor_pred_mom_yout.append(0.0)
                cc.stor_pred_mom_mag.append(0.0)
                cc.stor_internal_momx.append(0.0)
                cc.stor_internal_momy.append(0.0)
                cc.stor_v_rel.append(0.0)
                cc.stor_vx_rel.append(0.0)
                cc.stor_vy_rel.append(0.0)
                cc.stor_vel_ang_acc.append(0.0)
                cc.stor_vel_ang_diff.append(0.0)
                

        



    
