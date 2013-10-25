#!/usr/bin/env python

FortranCode = \
"""
subroutine vinterpol(im,jm,nin,nout,xin,yin,xout,extrap,yout,fill_value)

  integer, intent(in)                :: im,jm,nin,nout,extrap
  real, intent(in)                   :: fill_value
  real, intent(in), dimension(nin,jm,im)   :: xin
  real, intent(in), dimension(nin,jm,im)   :: yin
  real, intent(in), dimension(nout,jm,im)  :: xout
  real, intent(out), dimension(nout,jm,im) :: yout
  !f2py intent(in,hide) im,jm,nin,nout

  do i = 1,im
    do j = 1,jm
        call interpol(nin,nout,xin(:,j,i),yin(:,j,i),xout(:,j,i),extrap,yout(:,j,i),fill_value)
    enddo
  enddo

end subroutine vinterpol
!-------------------------------------------------------------
subroutine interpol(nin,nout,xin,yin,xout,extrap,yout,fill_value)

  integer, intent(in)                :: nin,nout,extrap
  real, intent(in)                   :: fill_value
  real, intent(in), dimension(nin)   :: xin
  real, intent(in), dimension(nin)   :: yin
  real, intent(in), dimension(nout)  :: xout
  real, intent(out), dimension(nout) :: yout
!f2py intent(in,hide) nin,nout

  ! Local
  real, allocatable, dimension(:)  :: spl

  allocate(spl(nin))
  yp1=1.e30
  ypn=1.e30
  call spline(xin,yin,nin,yp1,ypn,spl) 

  do n=2,nout-1
    if (extrap == 0 .and. ((xout(n)<xin(1)).or.(xout(n)>xin(nin)))) then
!    ((xout(n) < xin(1) .and. xout(n+1) < xin(1)) .or. &
!    (xout(n-1) > xin(nin) .and. xout(n) > xin(nin)))) then
      yout(n) = fill_value
    else
      call splint(xin,yin,spl,nin,xout(n),yout(n))
    endif
  enddo

  n=1
  if (extrap == 0 .and. &
    ((xout(n) < xin(1) .and. xout(n+1) < xin(1)) .or. &
    (xout(n) > xin(nin)))) then
        yout(n) = fill_value
    else
      call splint(xin,yin,spl,nin,xout(n),yout(n))
   endif

  n=nout
  if (extrap == 0 .and. &
    (xout(n) < xin(1) .or. &
    (xout(n-1) > xin(nin) .and. xout(n) > xin(nin)))) then
        yout(n) = fill_value
    else
      call splint(xin,yin,spl,nin,xout(n),yout(n))
   endif

end subroutine interpol
!------------------------------------------------------------------------
SUBROUTINE spline(x,y,n,yp1,ypn,y2)
  INTEGER n,NMAX
  REAL yp1,ypn,x(n),y(n),y2(n)
  PARAMETER (NMAX=500)
  INTEGER i,k
  REAL p,qn,sig,un,u(NMAX)
  if (yp1.gt..99e30) then
     y2(1)=0.
     u(1)=0.
  else
     y2(1)=-0.5
     u(1)=(3./(x(2)-x(1)))*((y(2)-y(1))/(x(2)-x(1))-yp1)
  endif
  do i=2,n-1
     sig=(x(i)-x(i-1))/(x(i+1)-x(i-1))
     p=sig*y2(i-1)+2.
     y2(i)=(sig-1.)/p
     u(i)=(6.*((y(i+1)-y(i))/(x(i+1)-x(i))-(y(i)-y(i-1))/ &
          (x(i)-x(i-1)))/(x(i+1)-x(i-1))-sig*u(i-1))/p
  end do
  if (ypn.gt..99e30) then
     qn=0.
     un=0.
  else
     qn=0.5
     un=(3./(x(n)-x(n-1)))*(ypn-(y(n)-y(n-1))/(x(n)-x(n-1)))
  endif
  y2(n)=(un-qn*u(n-1))/(qn*y2(n-1)+1.)
  do k=n-1,1,-1
     y2(k)=y2(k)*y2(k+1)+u(k)
  end do
  return
END SUBROUTINE spline
!----------------------------------------------------------------------
SUBROUTINE splint(xa,ya,y2a,n,x,y)
  INTEGER n
  REAL x,y,xa(n),y2a(n),ya(n)
  INTEGER k,khi,klo
  REAL a,b,h
  klo=1
  khi=n
1 if (khi-klo.gt.1) then
     k=(khi+klo)/2
     if(xa(k).gt.x)then
        khi=k
     else
        klo=k
     endif
     goto 1
  endif
  h=xa(khi)-xa(klo)
  if (h.eq.0.) stop 'bad xa input in splint'
  a=(xa(khi)-x)/h
  b=(x-xa(klo))/h
  y=a*ya(klo)+b*ya(khi)+((a**3-a)*y2a(klo)+(b**3-b)*y2a(khi))*(h**2)/6.
END SUBROUTINE splint
"""

import os,sys
from numpy import ma

try:
    import _interpol
except:
    f = open('interpol.f90','w')
    f.writelines(FortranCode)
    f.close()
    os.system('f2py -c -m _interpol interpol.f90')
    os.system('rm -f interpol.f90')
    import _interpol

def interpol(xin,yin,xout,Extrapolate=False):
    assert xin[0] < xin[-1], 'xin[0] > xin[-1]'
    if Extrapolate:
        extrap = 1
    else:
        extrap = 0
    yout = _interpol.interpol(xin,yin,xout,extrap,1.e20)
    if not Extrapolate:
        yout = ma.array( yout, mask = yout==1.e20 )
    return yout

def vinterpol(xin,yin,xout,Extrapolate=False,FillValue=1.e20):
    if Extrapolate:
        yout = _interpol.vinterpol(xin,yin,xout,1,FillValue)
    else:
        yout = _interpol.vinterpol(xin,yin,xout,0,FillValue)
        yout = ma.array( yout, mask = yout==FillValue )
    return yout


if __name__ == '__main__':
    import pylab as p
    xin = p.arange(20)*1.
    yin = xin**2
    xout = p.arange(25)/25.*20.+10.
    yout = interpol(xin,yin,xout)
    for i in range(len(yout)): print yout[i]
    p.plot(xin,yin,'b-o',xout,yout,'r-o')
    p.show()
