import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import z from 'zod';
import { useContext, useEffect } from 'react';
import { StoreContext } from '@/store/storeContext';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '../components/ui/form';
import { useLocation, useNavigate } from 'react-router-dom';
import { observer } from 'mobx-react-lite';
import { Auth } from '@/layouts/Auth.tsx';
import { Spinner } from '@/components/ui/spinner.tsx';

const formSchema = z.object({
  username: z.string().min(1, { message: 'Username is required' }),
  password: z.string().min(1, { message: 'Password is required' }),
});
export const Login = observer(() => {
  const location = useLocation();
  const store = useContext(StoreContext);
  const navigate = useNavigate();

  // Redirect if user already logged in
  useEffect(() => {
    if (store.isAuthRequired) {
      return;
    }

    const redirectUrl = location.state?.from?.pathname
      ? location.state.from.pathname + location.state?.from?.search
      : '/';
    navigate(redirectUrl, { replace: true });
  }, [store.isAuthRequired, location.state?.from?.pathname, location.state?.from?.search, navigate]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    await store.login(values);
  }

  return (
    <Auth>
      <div className="w-full max-w-sm min-w-xs">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Sign in to your account</CardTitle>
                <CardDescription>Enter your username and password below</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-6 pb-3 text-left">
                  <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                      <FormItem className="gap-3">
                        <FormLabel>Username</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter your username" autoComplete="username" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem className="gap-3">
                        <div className="flex items-center">
                          <FormLabel>Password</FormLabel>
                        </div>
                        <FormControl>
                          <Input type="password" autoComplete="password" placeholder="Enter your password" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
                    {form.formState.isSubmitting && <Spinner />}
                    Sign in
                  </Button>
                </div>
              </CardContent>
            </Card>
          </form>
        </Form>
      </div>
    </Auth>
  );
});
