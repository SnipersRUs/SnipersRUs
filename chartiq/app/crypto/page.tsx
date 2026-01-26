import CryptoNewsWidget from '@/components/CryptoNewsWidget';

export default function CryptoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-orange-950/20">
      <div className="container mx-auto py-8">
        <CryptoNewsWidget />
      </div>
    </div>
  );
}
