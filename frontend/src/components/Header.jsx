export default function Header() {
  return (
    <header className="bg-fmc-surface border-b border-fmc-accent-deep/60 px-6 py-3 flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <h1 className="text-xl font-mono font-bold text-fmc-text tracking-tight">
            <span className="text-fmc-accent">▸</span> find_my_car
          </h1>
          <p className="text-xs text-fmc-text-dim font-mono mt-0.5">
            Powered by LeBonCoin
          </p>
        </div>
        <div className="text-right text-xs text-fmc-text-dim font-mono">
          scanner · filtrer · trouver
        </div>
      </div>
    </header>
  );
}
