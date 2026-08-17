import { Button } from '@/components/ui/button.tsx';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.tsx';
import { observer } from 'mobx-react-lite';
import { useContext, useState } from 'react';
import { StoreContext } from '@/store/storeContext.ts';
import { Navigate, useNavigate } from 'react-router-dom';

export const Setup = observer(() => {
  const store = useContext(StoreContext);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const submit = async () => {
    setIsLoading(true);
    const success = await store.initializeDatabase();
    if (success) {
      navigate('/setup/auth', { replace: true });
    }
    setIsLoading(false);
  };

  if (!isLoading && !store.isSetupRequired) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-svh w-full flex-col items-center justify-start gap-8 px-3 py-16 text-left">
      <div className="flex items-center justify-center gap-2.5">
        <img src="logo.png" alt="Faved logo" className="h-auto w-[30px]" />
        <h2 className="text-2xl font-semibold tracking-tight">Faved</h2>
      </div>
      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle className="text-lg">Welcome to Faved!</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-8">
          <p>Before you can use the application, we need to set up the database. Click the button below to proceed.</p>

          <div className="rounded-lg bg-blue-100 p-4 dark:bg-blue-600">
            <p className="italic">
              <strong>Note:</strong> This will create a database file in the <code>/storage</code> folder of your
              application installation directory.
            </p>
          </div>
          <Button className="w-full" disabled={isLoading} onClick={submit}>
            {isLoading ? 'Creating Database...' : 'Create Database'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
});
