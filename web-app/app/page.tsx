import { getChatGPTUser, chatGPTSignInPath } from './chatgpt-auth';
import Dashboard from './dashboard';
export const dynamic = 'force-dynamic';
export default async function Home() {
  const identity = await getChatGPTUser();
  if (identity) return <Dashboard />;
  return <main className="login-shell"><div className="login-card"><a className="brand" href="/">✚ <span>Clin<span className="accent">IQ</span></span></a><p className="eyebrow">منصة الرعاية الصحية</p><h1>رعايتك تبدأ من هنا.</h1><p className="lead">اعثر على طبيبك، احجز موعدًا مناسبًا، وتابع حجوزاتك من مكان واحد.</p><a className="primary full" href={chatGPTSignInPath('/')} target="_top">الدخول أو إنشاء حساب باستخدام ChatGPT ←</a><p className="hint">يُنشأ حسابك تلقائيًا عند أول تسجيل دخول. يتطلب الدخول حساب ChatGPT.</p><div className="login-benefits"><span>✦ أطباء يضيفهم مدير المنصة</span><span>◷ مواعيد متاحة مباشرة</span><span>✓ إدارة حجوزاتك بسهولة</span></div></div><aside className="login-visual"><div className="orb"/><div className="hero-copy"><span className="pill">CLINIQ HEALTH</span><h2>صحتك في<br/>إيد أمينة.</h2><p>تجربة بسيطة تربط المريض بالطبيب، في الوقت المناسب.</p></div><div className="float-card">✚ <span>خطوة أقرب لصحة أفضل</span></div></aside></main>;
}
