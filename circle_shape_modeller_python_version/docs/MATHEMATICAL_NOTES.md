# Mathematical notes and interpretation

## Common external tangent contact geometry

Let `v=P2-P1`, `d=||v||`, `u=v/d`, and `n=(-u_y,u_x)`. A unit normal `N` to a common external tangent satisfies `N·u=(r1-r2)/d`. The two solutions are `N±=alpha*u ± sqrt(1-alpha²)*n`, where `alpha=(r1-r2)/d`. The line of contact has endpoints `P1+r1*N` and `P2+r2*N`. Real solutions require `d>0` and `|r1-r2|<=d`.

## Cubic Hermite interpolation

`H(t)=h00 P0+h10 M0+h01 P1+h11 M1`, with `h00=2t³-3t²+1`, `h10=t³-2t²+t`, `h01=-2t³+3t²`, and `h11=t³-t²`. Endpoint positions are exact: `H(0)=P0`, `H(1)=P1`; endpoint derivatives are `H'(0)=M0`, `H'(1)=M1`. The implementation chooses tangent handles parallel to the centreline chord, with magnitude `0.85d`.

## Bézier centreline and radius

For `m+1` control circles, `B(t)=Σ b_i^m(t)P_i` and `R(t)=Σ b_i^m(t)r_i`, where `b_i^m(t)=C(m,i)(1-t)^(m-i)t^i`. The derivative can be evaluated as `B'(t)=m Σ b_i^(m-1)(t)(P_(i+1)-P_i)`. The unit normal is perpendicular to `B'(t)`. The offsets `B±RN` are geometrically meaningful as normal offsets, but they do not generally coincide with the exact envelope of all translated disks.
