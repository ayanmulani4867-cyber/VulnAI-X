declare module 'lucide-react' {
  import React from 'react';

  export interface LucideProps extends React.SVGProps<SVGSVGElement> {
    size?: string | number;
    color?: string;
    strokeWidth?: string | number;
    className?: string;
  }

  export type LucideIcon = React.FC<LucideProps>;

  export const LayoutDashboard: LucideIcon;
  export const ShieldCheck: LucideIcon;
  export const PlayCircle: LucideIcon;
  export const AlertTriangle: LucideIcon;
  export const FileText: LucideIcon;
  export const Cpu: LucideIcon;
  export const Mail: LucideIcon;
  export const Activity: LucideIcon;
  export const AlertOctagon: LucideIcon;
  export const LogOut: LucideIcon;
  export const User: LucideIcon;
  export const StopCircle: LucideIcon;
  export const RefreshCw: LucideIcon;
  export const Plus: LucideIcon;
  export const Terminal: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const Eye: LucideIcon;
  export const Filter: LucideIcon;
  export const CheckCircle: LucideIcon;
  export const CheckCircle2: LucideIcon;
  export const ShieldAlert: LucideIcon;
  export const Download: LucideIcon;
  export const Code: LucideIcon;
  export const Compass: LucideIcon;
  export const Globe: LucideIcon;
  export const Smartphone: LucideIcon;
  export const Cloud: LucideIcon;
  export const Bot: LucideIcon;
  export const Layers: LucideIcon;
  export const Send: LucideIcon;
  export const Database: LucideIcon;
  export const Lock: LucideIcon;
  export const PauseCircle: LucideIcon;
  export const Trash2: LucideIcon;
  export const ExternalLink: LucideIcon;
  export const Flame: LucideIcon;
  export const XCircle: LucideIcon;
  export const Clock: LucideIcon;
  export const X: LucideIcon;
  
  const icons: Record<string, LucideIcon>;
  export default icons;
}
